# backend/app/routes/history.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.db import get_session
from app.crud import list_runs

router = APIRouter()

class RunOut(BaseModel):
    id: int
    run_type: str
    source: str | None
    created_at: str
    output_text: str | None

@router.get("/history", response_model=List[RunOut])
async def history(limit: int = 50, db: AsyncSession = Depends(get_session)):
    """
    Return recent research runs (most recent first).
    Trim long outputs to keep payloads small.
    """
    runs = await list_runs(db, limit=limit)
    out = []
    for r in runs:
        out.append(RunOut(
            id=r.id,
            run_type=r.run_type,
            source=r.source,
            created_at=r.created_at.isoformat() if r.created_at is not None else None,
            output_text=(r.output_text[:500] + "...") if r.output_text and len(r.output_text) > 500 else r.output_text,
        ))
    return out
