import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Always load backend/.env regardless of where the command is run from
repo_root = Path(__file__).resolve().parents[1]  # backend/
load_dotenv(dotenv_path=repo_root / ".env")

from .db import engine, Base  # import AFTER loading env

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

if __name__ == "__main__":
    asyncio.run(create_all())