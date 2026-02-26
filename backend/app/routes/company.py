# backend/app/routes/company.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
import httpx, trafilatura, os

router = APIRouter()
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

class Body(BaseModel):
    url: HttpUrl
    bullets: int = 6

@router.post("/company/summary")
async def company_summary(body: Body):
    # 1) fetch page
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as c:
      r = await c.get(str(body.url))
      r.raise_for_status()
    html = r.text

    # 2) extract readable text
    text = trafilatura.extract(html, favor_recall=True) or ""
    if not text.strip():
        raise HTTPException(400, "Could not extract readable text from page")

    # 3) prompt → ollama
    prompt = (
      f"Summarize this company's website in {body.bullets} concise bullets. "
      "Focus on what they do, ICP, products, recent news, any tech stack signals.\n\n"
      f"TEXT:\n{text[:12000]}"
    )

    async with httpx.AsyncClient(timeout=90) as c:
      r = await c.post(f"{OLLAMA_BASE}/api/generate",
                       json={"model": MODEL, "prompt": prompt, "stream": False})
      if r.status_code == 404:  # newer Ollama
        r = await c.post(f"{OLLAMA_BASE}/api/chat",
                         json={"model": MODEL, "messages":[{"role":"user","content": prompt}],
                               "stream": False})
      r.raise_for_status()
      data = r.json()

    summary = (data.get("response") or data.get("message", {}).get("content") or "").strip()
    return {"summary": summary, "source": str(body.url)}
