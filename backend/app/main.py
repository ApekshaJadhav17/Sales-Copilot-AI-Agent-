from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent /  ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.summarize import router as summarize_router

from app.routes.company import router as company_router

from app.routes.upload import router as upload_router

from app.routes.report import router as report_router




import os
print("--------------------ENV OLLAMA_MODEL =", os.getenv("OLLAMA_MODEL"))

import os
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5174")


app = FastAPI(title="Sales Copilot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173",  "http://127.0.0.1:5173", "http://127.0.0.1:5174"],  # your frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(summarize_router, prefix="/api")
app.include_router(company_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(report_router, prefix="/api")

