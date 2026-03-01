# backend/app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .db import Base

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import JSON

class ResearchRun(Base):
    __tablename__ = "research_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String(50), nullable=False)        # e.g. "company_summary", "prospect_upload", "precall_report", "summarize"
    input_text = Column(Text, nullable=True)             # raw input (url, pasted text, or file-extracted text)
    input_meta = Column(Text, nullable=True)             # small JSON-like string or metadata
    output_text = Column(Text, nullable=True)            # model response
    source = Column(String(1024), nullable=True)         # e.g. original URL or filename
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="chunks")

    embedding = Column(JSON, nullable=True)