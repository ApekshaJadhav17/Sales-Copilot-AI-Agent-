from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx, os

router = APIRouter()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instrcut")


class SummarizeBody(BaseModel):
    text: str
    bullets: int = 5

@router.post("/summarize")

async def summarize(body: SummarizeBody):
    prompt = (
        f"Summarize the following text in {body.bullets} bullet points. "
        "Be concise and factual.\n\n" + body.text
    )
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Ollama generate API (non-stream)
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            r.raise_for_status()
            data = r.json()
            return {"summary": data.get("response", "").strip()}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e}")