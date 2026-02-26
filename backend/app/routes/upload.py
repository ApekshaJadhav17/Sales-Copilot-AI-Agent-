from fastapi import APIRouter, UploadFile, File, HTTPException
from PyPDF2 import PdfReader
from io import BytesIO
import os, httpx

router = APIRouter()
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

def pdf_to_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

@router.post("/prospect/upload")
async def prospect_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")
    data = await file.read()
    text = pdf_to_text(data)
    if len(text) < 120:
        raise HTTPException(400, "Could not extract enough text from PDF.")

    prefix = ("Extract prospect insights in concise bullets: role & seniority, interests, current focus, "
              "possible pains, and 1–2 personalized hooks. Return 5–7 bullets.\n\n")
    prompt = prefix + text[:12000]

    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(f"{OLLAMA_BASE}/api/generate",
                         json={"model": MODEL, "prompt": prompt, "stream": False})
        if r.status_code == 404:
            r = await c.post(f"{OLLAMA_BASE}/api/chat",
                             json={"model": MODEL, "messages":[{"role":"user","content": prompt}],
                                   "stream": False})
        r.raise_for_status()
        data = r.json()

    summary = (data.get("response") or data.get("message", {}).get("content") or "").strip()
    return {"summary": summary}
