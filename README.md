# 🧠 Sales Copilot — AI-Powered Sales Research Assistant (Local GenAI App)

A privacy-first, full-stack Generative AI app that automates company and prospect research to generate pre-call briefings — powered entirely by local LLMs (via Ollama).

## 📘 Overview

Sales Copilot is an intelligent sales enablement tool built with React (TypeScript) on the frontend and FastAPI (Python) on the backend.
It uses a local LLM (Llama 3) via Ollama to summarize company websites, analyze LinkedIn profile PDFs, and compose detailed Pre-Call Reports — all running 100% locally, ensuring zero API cost and full data privacy.

The MVP demonstrates an end-to-end AI workflow:

**Company Researcher:** Crawl a company website and summarize it.

**Prospect Researcher:** Extract text from LinkedIn profile PDFs or pasted content to generate personalized insights.

**Summarizer:** Summarize any arbitrary text.

**Pre-Call Report:** Combine company + prospect summaries into a polished, actionable briefing.

##⚙️ Tech Stack
### 🧩 Frontend

React 18 + TypeScript

Vite for bundling & dev server

Tailwind CSS (Apple-style glassmorphism UI)

React Query (@tanstack/react-query) for async state management

React Markdown for rendering AI-generated markdown output

### 🧠 Backend

FastAPI — lightweight async Python web framework

Pydantic — input validation

httpx — async HTTP client for model communication

Trafilatura — web crawler & content cleaner

pypdf — PDF text extraction

Redis / PostgreSQL (planned) — caching & storage

Docker — environment consistency

### 🤖 AI / LLM Integration

Ollama running Llama 3 locally (ollama serve)

Prompt-based summarization, research & report generation

Optional vector DB integration for RAG (future upgrade)
