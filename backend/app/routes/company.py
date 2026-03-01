# backend/app/routes/company.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
import httpx, trafilatura, os
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.crud import create_run
from app.models import Source, Chunk
from app.services.embeddings import embed_texts

# Pinecone helper
from app.services.vector_store import query_similar_chunks

# embed core (ensures postgres embeddings + upsert logic)
from app.routes.embed import embed_source_chunks_core

router = APIRouter()

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")


class Body(BaseModel):
    url: HttpUrl
    bullets: int = 6
    debug: bool = False


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


async def get_or_create_source(db: AsyncSession, url: str, raw_text: str) -> Source:
    res = await db.execute(select(Source).where(Source.url == url).limit(1))
    existing = res.scalar_one_or_none()
    if existing:
        return existing

    s = Source(url=url, raw_text=(raw_text or "")[:200000])
    db.add(s)
    await db.flush()
    return s


async def get_chunks_for_source(db: AsyncSession, source_id: int) -> list[Chunk]:
    res = await db.execute(
        select(Chunk)
        .where(Chunk.source_id == source_id)
        .order_by(Chunk.chunk_index.asc())
    )
    return list(res.scalars().all())


@router.post("/company/summary")
async def company_summary(body: Body, db: AsyncSession = Depends(get_session)):
    url = str(body.url)

    # 1) Fetch page
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, connect=30.0),
            headers={"User-Agent": "Mozilla/5.0 (SalesCopilot/0.1)"},
        ) as c:
            r = await c.get(url)
            r.raise_for_status()
            html = r.text
    except httpx.ConnectError as e:
        raise HTTPException(503, f"Could not reach target URL. {repr(e)}")
    except httpx.ReadTimeout:
        raise HTTPException(504, "Timed out while fetching the page.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(400, f"Error fetching page: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(503, f"Request error while fetching page: {repr(e)}")

    # 2) Extract readable text
    text = trafilatura.extract(html, favor_recall=True) or ""
    if not text.strip():
        raise HTTPException(400, "Could not extract readable text from page")

    # 3) Store source + chunks, then embed via embed core and retrieve via Pinecone
    source = None
    context = text[:12000]

    try:
        source = await get_or_create_source(db, url=url, raw_text=text)

        chunks = await get_chunks_for_source(db, source.id)
        if not chunks:
            pieces = chunk_text(text, chunk_size=900, overlap=120)
            for i, ch in enumerate(pieces):
                db.add(Chunk(source_id=source.id, chunk_index=i, chunk_text=ch[:5000]))
            await db.commit()
            chunks = await get_chunks_for_source(db, source.id)

        # Ensure embeddings + upsert to Pinecone (non-blocking best-effort inside)
        try:
            await embed_source_chunks_core(db, source.id, force=False)
        except Exception as e:
            print("Warning: embed_core failed for company summary:", repr(e))

        # Retrieval via Pinecone
        retrieval_query = (
            "Summarize the company: what they do, ideal customer profile (ICP), "
            "products/offerings, any recent strategic notes/news, and tech stack signals."
        )
        try:
            qv = embed_texts([retrieval_query])[0]
            matches = query_similar_chunks(query_vector=qv, top_k=5, source_id=source.id)
            top_chunks = [m.get("metadata", {}).get("chunk_text", "") for m in matches]
            if top_chunks and any(top_chunks):
                context = "\n\n---\n\n".join(top_chunks)[:12000]
            else:
                context = text[:12000]
        except Exception as e:
            print("Warning: Pinecone query failed for company summary:", repr(e))
            context = text[:12000]

    except Exception as e:
        print("Warning: company RAG prep failed, falling back to raw text:", repr(e))
        context = text[:12000]

    # 4) Prompt → Ollama
    prompt = (
        f"Summarize this company's website in {body.bullets} concise bullets. "
        "Focus on what they do, ICP, products, recent strategic notes/news, and tech stack signals.\n\n"
        f"CONTEXT:\n{context}"
    )

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False},
        )
        if r.status_code == 404:
            r = await c.post(
                f"{OLLAMA_BASE}/api/chat",
                json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False},
            )
        r.raise_for_status()
        data = r.json()

    summary = (data.get("response") or data.get("message", {}).get("content") or "").strip()

    # 5) Persist run (don’t fail the request if DB write fails)
    try:
        await create_run(
            db,
            run_type="company_summary_rag",
            input_text=context[:20000],
            output_text=summary,
            source=url,
        )
    except Exception as e:
        print("Warning: persist failed (company_summary_rag):", repr(e))

    resp = {"summary": summary, "source": url}
    if body.debug:
        resp["rag"] = {
            "source_id": (source.id if source else None),
            "context_preview": context[:600],
        }
    return resp


# # backend/app/routes/company.py

# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel, HttpUrl
# import httpx, trafilatura, os
# import numpy as np
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

# from app.db import get_session
# from app.crud import create_run
# from app.models import Source, Chunk
# from app.services.embeddings import embed_texts

# from app.services.vector_store import upsert_chunk_embeddings

# router = APIRouter()

# OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")


# class Body(BaseModel):
#     url: HttpUrl
#     bullets: int = 6
#     debug: bool = False


# def cosine(a: np.ndarray, b: np.ndarray) -> float:
#     # embeddings are normalized -> cosine == dot product
#     return float(np.dot(a, b))


# def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
#     text = (text or "").strip()
#     if not text:
#         return []
#     chunks: list[str] = []
#     start = 0
#     n = len(text)
#     while start < n:
#         end = min(start + chunk_size, n)
#         chunks.append(text[start:end])
#         if end == n:
#             break
#         start = max(0, end - overlap)
#     return chunks


# async def get_or_create_source(db: AsyncSession, url: str, raw_text: str) -> Source:
#     res = await db.execute(select(Source).where(Source.url == url).limit(1))
#     existing = res.scalar_one_or_none()
#     if existing:
#         return existing

#     s = Source(url=url, raw_text=(raw_text or "")[:200000])
#     db.add(s)
#     await db.flush()  # assigns s.id
#     return s


# async def get_chunks_for_source(db: AsyncSession, source_id: int) -> list[Chunk]:
#     res = await db.execute(
#         select(Chunk)
#         .where(Chunk.source_id == source_id)
#         .order_by(Chunk.chunk_index.asc())
#     )
#     return list(res.scalars().all())


# # async def ensure_embeddings(db: AsyncSession, chunks: list[Chunk]) -> int:
# #     missing = [c for c in chunks if not getattr(c, "embedding", None)]
# #     if not missing:
# #         return 0

# #     vecs = embed_texts([c.chunk_text for c in missing])

# #     #for pincone upsert


# # # after computing vecs = embed_texts([...])
# #     items = []
# #     for c, v in zip(missing, vecs):
# #       c.embedding = v
# #       items.append({
# #         "id": f"chunk:{c.id}",          # pinecone vector id
# #         "values": v,
# #         "metadata": {
# #         "chunk_id": c.id,
# #         "source_id": c.source_id,
# #         "chunk_index": c.chunk_index,
# #         "chunk_text": c.chunk_text[:1000],
# #         }
# #     })

# #     await db.commit()
# #     upsert_chunk_embeddings(items)
# #     for c, v in zip(missing, vecs):
# #       c.embedding = v

# #     await db.commit()
# #     return len(missing)


# async def ensure_embeddings(db: AsyncSession, chunks: list[Chunk]) -> int:
#     missing = [c for c in chunks if not getattr(c, "embedding", None)]
#     if not missing:
#         return 0

#     vecs = embed_texts([c.chunk_text for c in missing])

#     # 1) Save embeddings to Postgres
#     for c, v in zip(missing, vecs):
#         c.embedding = v

#     await db.commit()  # commit once

#     # 2) Upsert to Pinecone (best-effort; don't fail request if Pinecone is down)
#     try:
#         from app.services.vector_store import upsert_chunk_embeddings

#         items = []
#         for c, v in zip(missing, vecs):
#             items.append(
#                 {
#                     "id": f"chunk:{c.id}",  # pinecone vector id
#                     "values": v,
#                     "metadata": {
#                         "chunk_id": c.id,
#                         "source_id": c.source_id,
#                         "chunk_index": c.chunk_index,
#                         "chunk_text": c.chunk_text[:1000],
#                     },
#                 }
#             )

#         upsert_chunk_embeddings(items)

#     except Exception as e:
#         print("Warning: Pinecone upsert failed:", repr(e))

#     return len(missing)


# async def retrieve_top_chunks(
#     db: AsyncSession, query: str, source_id: int, top_k: int = 5
# ) -> list[str]:
#     res = await db.execute(
#         select(Chunk).where(
#             Chunk.source_id == source_id,
#             Chunk.embedding.is_not(None),
#         )
#     )
#     chunks = list(res.scalars().all())
#     if not chunks:
#         return []

#     qv = np.array(embed_texts([query])[0], dtype=float)

#     scored: list[tuple[float, Chunk]] = []
#     for c in chunks:
#         v = np.array(c.embedding, dtype=float)
#         scored.append((cosine(qv, v), c))

#     scored.sort(key=lambda x: x[0], reverse=True)
#     top = scored[: max(1, min(top_k, 20))]

#     return [c.chunk_text for score, c in top]


# @router.post("/company/summary")
# async def company_summary(body: Body, db: AsyncSession = Depends(get_session)):
#     url = str(body.url)

#     # 1) Fetch page
#     try:
#         async with httpx.AsyncClient(
#             follow_redirects=True,
#             timeout=httpx.Timeout(30.0, connect=30.0),
#             headers={"User-Agent": "Mozilla/5.0 (SalesCopilot/0.1)"},
#         ) as c:
#             r = await c.get(url)
#             r.raise_for_status()
#             html = r.text
#     except httpx.ConnectError as e:
#         raise HTTPException(503, f"Could not reach target URL. {repr(e)}")
#     except httpx.ReadTimeout:
#         raise HTTPException(504, "Timed out while fetching the page.")
#     except httpx.HTTPStatusError as e:
#         raise HTTPException(400, f"Error fetching page: {e.response.status_code}")
#     except httpx.RequestError as e:
#         raise HTTPException(503, f"Request error while fetching page: {repr(e)}")

#     # 2) Extract readable text
#     text = trafilatura.extract(html, favor_recall=True) or ""
#     if not text.strip():
#         raise HTTPException(400, "Could not extract readable text from page")

#     # 3) RAG: store source + chunks, embed if needed, retrieve top chunks
#     try:
#         source = await get_or_create_source(db, url=url, raw_text=text)

#         chunks = await get_chunks_for_source(db, source.id)
#         if not chunks:
#             pieces = chunk_text(text, chunk_size=900, overlap=120)
#             for i, ch in enumerate(pieces):
#                 db.add(
#                     Chunk(
#                         source_id=source.id,
#                         chunk_index=i,
#                         chunk_text=ch[:5000],
#                     )
#                 )
#             await db.commit()
#             chunks = await get_chunks_for_source(db, source.id)

#         await ensure_embeddings(db, chunks)

#         retrieval_query = (
#             "Summarize the company: what they do, ideal customer profile (ICP), "
#             "products/offerings, any recent strategic notes/news, and tech stack signals."
#         )
#         top_chunks = await retrieve_top_chunks(
#             db, retrieval_query, source_id=source.id, top_k=5
#         )
#         context = "\n\n---\n\n".join(top_chunks)[:12000]

#     except Exception as e:
#         # If anything in RAG prep fails, fall back to raw text (still return a summary)
#         print("Warning: RAG prep failed, falling back to raw text:", repr(e))
#         context = text[:12000]

#     # 4) Prompt → Ollama
#     prompt = (
#         f"Summarize this company's website in {body.bullets} concise bullets. "
#         "Focus on what they do, ICP, products, recent strategic notes/news, and tech stack signals.\n\n"
#         f"CONTEXT:\n{context}"
#     )

#     async with httpx.AsyncClient(timeout=120) as c:
#         r = await c.post(
#             f"{OLLAMA_BASE}/api/generate",
#             json={"model": MODEL, "prompt": prompt, "stream": False},
#         )
#         if r.status_code == 404:
#             r = await c.post(
#                 f"{OLLAMA_BASE}/api/chat",
#                 json={
#                     "model": MODEL,
#                     "messages": [{"role": "user", "content": prompt}],
#                     "stream": False,
#                 },
#             )
#         r.raise_for_status()
#         data = r.json()

#     summary = (data.get("response") or data.get("message", {}).get("content") or "").strip()

#     # 5) Persist run (don’t fail the request if DB write fails)
#     try:
#         await create_run(
#             db,
#             run_type="company_summary_rag",
#             input_text=context[:20000],
#             output_text=summary,
#             source=url,
#         )
#     except Exception as e:
#         print("Warning: persist failed (company_summary_rag):", e)

#     # return {"summary": summary, "source": url}
#     resp = {"summary": summary, "source": url}

#     if body.debug:
#       resp["rag"] = {
#         "source_id": source.id if "source" in locals() else None,
#         "context_preview": context[:600],
#       }

#     return resp