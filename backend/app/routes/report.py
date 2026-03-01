# backend/app/routes/report.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import os, httpx
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.crud import create_run
from app.models import Chunk
from app.services.embeddings import embed_texts

# Pinecone helpers (you already have these)
from app.services.vector_store import query_similar

router = APIRouter()

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")


class PrecallBody(BaseModel):
    company: str = Field(min_length=10, description="Company summary or notes")
    prospect: str = Field(min_length=10, description="Prospect insights or notes")
    tone: str | None = Field(default="concise, friendly, expert")


class PrecallRagBody(BaseModel):
    company_source_id: int
    prospect_source_id: int
    tone: str | None = Field(default="concise, friendly, expert")
    top_k: int = 5
    debug: bool = False


PROMPT_TEMPLATE = """You are an expert sales enablement writer.
Create a crisp, actionable pre-call briefing using the inputs.

Rules:
- Use gender-neutral language for the prospect.
- Only use facts present in the provided context. If something is not in context, write "Not specified in sources."
- Do not claim internships/opportunities unless explicitly present.

TONE: {tone}

SECTIONS (use clear headings & bullet points):
1) Snapshot
   - Who the company is, what they do, 2-3 recent/strategic notes
   - Prospect role & seniority, 2-3 interests or focus areas
2) Talking Points (5 bullets)
3) Personalized Hooks (3 bullets)
4) Likely Objections & Short Answers (3 bullets)
5) CTA (1-2 lines)

Inputs:
[COMPANY]
{company}

[PROSPECT]
{prospect}
"""


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    # embeddings normalized -> cosine == dot product
    return float(np.dot(a, b))


async def call_ollama(prompt: str) -> str:
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
    return (data.get("response") or data.get("message", {}).get("content") or "").strip()


# ----------------------------
# Local DB embedding utilities
# ----------------------------
async def ensure_source_embeddings(db: AsyncSession, source_id: int) -> int:
    """
    Ensures Postgres chunks for this source have embeddings.
    Note: embedding computation is local; Pinecone upsert is handled elsewhere (embed endpoint).
    """
    res = await db.execute(select(Chunk).where(Chunk.source_id == source_id))
    chunks = list(res.scalars().all())
    if not chunks:
        return 0

    missing = [c for c in chunks if not getattr(c, "embedding", None)]
    if not missing:
        return 0

    vecs = embed_texts([c.chunk_text for c in missing])
    for c, v in zip(missing, vecs):
        c.embedding = v

    await db.commit()
    return len(missing)


async def local_retrieve_top_chunks(
    db: AsyncSession, query: str, source_id: int, top_k: int
) -> list[dict]:
    """
    Fallback retrieval from Postgres using cosine similarity.
    """
    res = await db.execute(
        select(Chunk).where(
            Chunk.source_id == source_id,
            Chunk.embedding.is_not(None),
        )
    )
    chunks = list(res.scalars().all())
    if not chunks:
        return []

    qv = np.array(embed_texts([query])[0], dtype=float)
    scored: list[tuple[float, Chunk]] = []
    for c in chunks:
        v = np.array(c.embedding, dtype=float)
        scored.append((cosine(qv, v), c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: max(1, min(top_k, 20))]

    return [
        {"score": float(score), "chunk_index": c.chunk_index, "chunk_text": c.chunk_text}
        for score, c in top
    ]


# ----------------------------
# Pinecone retrieval utilities
# ----------------------------
async def pinecone_retrieve_top_chunks(
    db: AsyncSession, query: str, source_id: int, top_k: int
) -> tuple[list[dict], str | None]:
    """
    Retrieves top chunks via Pinecone, then resolves chunk_text from Postgres using metadata.chunk_id.
    Returns (hits, error_string_or_none)
    """
    try:
        qv = embed_texts([query])[0]

        pinecone_filter = {"source_id": {"$eq": source_id}}
        res = query_similar(
            query_vector=qv,
            top_k=max(1, min(top_k, 10)),
            filter=pinecone_filter,
        )

        matches = res.get("matches") if isinstance(res, dict) else getattr(res, "matches", None)
        if not matches:
            return [], None

        hits = []
        for m in matches:
            md = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {}) or {}
            score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
            chunk_id = md.get("chunk_id")

            if chunk_id is None:
                # still return metadata so debug doesn't break
                hits.append({"score": float(score) if score is not None else None, "chunk_index": None, "chunk_text": md.get("chunk_text", "")})
                continue

            row = await db.execute(select(Chunk).where(Chunk.id == int(chunk_id)).limit(1))
            ch = row.scalar_one_or_none()
            if not ch:
                # fallback to stored text in metadata
                hits.append({"score": float(score) if score is not None else None, "chunk_index": md.get("chunk_index"), "chunk_text": md.get("chunk_text", "")})
                continue

            hits.append(
                {
                    "score": float(score) if score is not None else None,
                    "chunk_index": ch.chunk_index,
                    "chunk_text": ch.chunk_text,
                }
            )

        return hits, None

    except Exception as e:
        # never crash; caller can fallback to local retrieval
        return [], f"{repr(e)}"


@router.post("/report/precall")
async def generate_precall(body: PrecallBody, db: AsyncSession = Depends(get_session)):
    prompt = PROMPT_TEMPLATE.format(
        company=body.company[:20000],
        prospect=body.prospect[:20000],
        tone=body.tone or "concise, friendly, expert",
    )

    try:
        content = await call_ollama(prompt)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Model server unreachable. Start `ollama serve`.")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Model timeout. Try shorter inputs.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e.response.text}")

    if not content:
        raise HTTPException(status_code=502, detail="Empty model response.")

    try:
        await create_run(
            db,
            run_type="precall_report",
            input_text=(body.company[:8000] + "\n\n" + body.prospect[:8000]),
            output_text=content,
            source=None,
        )
    except Exception as e:
        print("Warning: persist failed (precall_report):", e)

    return {"report_md": content}


@router.post("/report/precall_rag")
async def generate_precall_rag(body: PrecallRagBody, db: AsyncSession = Depends(get_session)):
    top_k = max(1, min(body.top_k, 10))

    # Ensure Postgres embeddings exist (so fallback retrieval works)
    try:
        await ensure_source_embeddings(db, body.company_source_id)
        await ensure_source_embeddings(db, body.prospect_source_id)
    except Exception as e:
        raise HTTPException(500, f"Embedding step failed: {repr(e)}")

    company_query = (
        "Extract: what the organization does, key services/responsibilities, who they serve, and any noteworthy programs or standards mentioned."
    )
    prospect_query = (
        "Extract: current title/role, seniority signals, skills/tech stack, current goals (internship/job), and 2 personalization hooks."
    )

    # 1) Try Pinecone retrieval first
    company_hits, company_pc_err = await pinecone_retrieve_top_chunks(db, company_query, body.company_source_id, top_k)
    prospect_hits, prospect_pc_err = await pinecone_retrieve_top_chunks(db, prospect_query, body.prospect_source_id, top_k)

    used = {"company": "pinecone", "prospect": "pinecone"}

    # 2) If Pinecone empty or failed, fallback to local DB similarity
    if not company_hits:
        company_hits = await local_retrieve_top_chunks(db, company_query, body.company_source_id, top_k)
        used["company"] = "local_db"
    if not prospect_hits:
        prospect_hits = await local_retrieve_top_chunks(db, prospect_query, body.prospect_source_id, top_k)
        used["prospect"] = "local_db"

    if not company_hits:
        raise HTTPException(400, "No company chunks found (neither Pinecone nor local). Ingest/embed company source first.")
    if not prospect_hits:
        raise HTTPException(400, "No prospect chunks found (neither Pinecone nor local). Upload/embed prospect PDF first.")

    company_context = "\n\n---\n\n".join([h.get("chunk_text", "") for h in company_hits])[:12000]
    prospect_context = "\n\n---\n\n".join([h.get("chunk_text", "") for h in prospect_hits])[:12000]

    prompt = PROMPT_TEMPLATE.format(
        company=company_context,
        prospect=prospect_context,
        tone=body.tone or "concise, friendly, expert",
    )

    try:
        report_md = await call_ollama(prompt)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Model server unreachable. Start `ollama serve`.")
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Model timeout. Try shorter inputs.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e.response.text}")

    if not report_md:
        raise HTTPException(status_code=502, detail="Empty model response.")

    try:
        await create_run(
            db,
            run_type="precall_report_rag",
            input_text=(company_context[:9000] + "\n\n" + prospect_context[:9000]),
            output_text=report_md,
            source=f"company:{body.company_source_id}|prospect:{body.prospect_source_id}",
        )
    except Exception as e:
        print("Warning: persist failed (precall_report_rag):", e)

    resp = {"report_md": report_md}

    if body.debug:
        resp["rag"] = {
            "company_source_id": body.company_source_id,
            "prospect_source_id": body.prospect_source_id,
            "retrieval_used": used,
            "company_top": [{"score": round((h.get("score") or 0.0), 4), "chunk_index": h.get("chunk_index")} for h in company_hits],
            "prospect_top": [{"score": round((h.get("score") or 0.0), 4), "chunk_index": h.get("chunk_index")} for h in prospect_hits],
            "company_context_preview": company_context[:600],
            "prospect_context_preview": prospect_context[:600],
            "pinecone_error_company": company_pc_err,
            "pinecone_error_prospect": prospect_pc_err,
        }

    return resp