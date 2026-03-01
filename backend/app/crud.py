# backend/app/crud.py
from sqlalchemy import select, desc
from .models import ResearchRun
from sqlalchemy.ext.asyncio import AsyncSession

async def create_run(db: AsyncSession, run_type: str, input_text: str | None, output_text: str | None, source: str | None = None, input_meta: str | None = None):
    new = ResearchRun(
        run_type=run_type,
        input_text=input_text,
        output_text=output_text,
        source=source,
        input_meta=input_meta,
    )
    db.add(new)
    await db.flush()   # get id populated
    await db.commit()
    await db.refresh(new)
    return new

async def list_runs(db: AsyncSession, limit: int = 50):
    q = select(ResearchRun).order_by(desc(ResearchRun.created_at)).limit(limit)
    res = await db.execute(q)
    return [r for (r,) in res.all()]