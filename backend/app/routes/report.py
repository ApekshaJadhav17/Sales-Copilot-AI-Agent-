# backend/app/routes/report.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os, httpx

router = APIRouter()

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

class PrecallBody(BaseModel):
    company: str = Field(min_length=10, description="Company summary or notes")
    prospect: str = Field(min_length=10, description="Prospect insights or notes")
    tone: str | None = Field(default="concise, friendly, expert")

PROMPT_TEMPLATE = """You are an expert sales enablement writer.
Create a crisp, actionable pre-call briefing using the inputs.

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

@router.post("/report/precall")
async def generate_precall(body: PrecallBody):
    prompt = PROMPT_TEMPLATE.format(
        company=body.company[:20000],
        prospect=body.prospect[:20000],
        tone=body.tone or "concise, friendly, expert",
    )

    async with httpx.AsyncClient(timeout=120) as c:
        try:
            # try /generate, fall back to /chat
            r = await c.post(f"{OLLAMA_BASE}/api/generate",
                             json={"model": MODEL, "prompt": prompt, "stream": False})
            if r.status_code == 404:
                r = await c.post(f"{OLLAMA_BASE}/api/chat",
                                 json={"model": MODEL,
                                       "messages":[{"role":"user","content":prompt}],
                                       "stream": False})
            r.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(status_code=503,
                detail="Model server unreachable. Start `ollama serve` (127.0.0.1:11434).")
        except httpx.ReadTimeout:
            raise HTTPException(status_code=504,
                detail="Model timeout. Try shorter inputs.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Model error: {e.response.text}")

    data = r.json()
    content = (data.get("response") or data.get("message", {}).get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="Empty model response.")
    return {"report_md": content}
