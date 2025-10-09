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

## ⚙️ Tech Stack
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


## Architecture 
                ┌─────────────────────────────┐
                │         React (Vite)        │
                │  Summarizer / Company /     │
                │  Prospect / Report UI       │
                └─────────────┬───────────────┘
                              │  JSON (REST)
                              ▼
                 ┌────────────────────────────┐
                 │         FastAPI API        │
                 │  /api/summarize            │
                 │  /api/company/summary      │
                 │  /api/prospect/upload      │
                 │  /api/report/precall       │
                 └─────────────┬──────────────┘
                               │  HTTP calls via httpx
                               ▼
                  ┌────────────────────────────┐
                  │          Ollama            │
                  │   Local Llama 3 model      │
                  │   127.0.0.1:11434          │
                  └─────────────┬──────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │   AI Generation    │
                     │ Summaries, Hooks,  │
                     │ Talking Points     │
                     └────────────────────┘





## 🔁 Query Flow

- **Frontend action** → User pastes text, enters a URL, or uploads a PDF.

- **Request**  → React sends an HTTP request to FastAPI (/api/* endpoints).

- **Processing** → FastAPI:

  ***1:Cleans/crawls data (Trafilatura)***

  ***2:Parses PDFs (pypdf)***

  ***3:Builds structured prompts***

  ***4:Calls the local LLM via httpx → Ollama REST API (/api/generate or /api/chat).***

- **Response** → LLM returns a summary or report.

- **Frontend renders** → Output displayed as Markdown on a glass UI card.



  ## Project Structure
  <img width="521" height="609" alt="image" src="https://github.com/user-attachments/assets/b5f6d5ce-b729-4631-a3ce-c3eb4443ecc6" />




## 🌟 Key Features Explained
### 🧠 Local AI Summarization

Uses Llama 3 (8B) via Ollama to generate bullet-point summaries.

Completely offline & private — no data leaves your machine.

Supports both /api/generate and /api/chat API versions for compatibility.

### 🌐 Company Researcher

Crawls company websites with Trafilatura.

Extracts main readable text (strips ads, menus, boilerplate).

Summarizes into concise company overview with ICP, products, and pain points.

### 👤 Prospect Researcher

Accepts either:

Pasted profile text

LinkedIn PDF export

Parses text with pypdf and generates 5–7 bullets:

Role & seniority

Interests & focus

Potential pain points

Personalized outreach hooks

###🧾 Pre-Call Report Generator

Combines company + prospect summaries.

Produces a structured markdown report with:

Snapshot

Talking Points

Personalized Hooks

Likely Objections + Answers

CTA

Tailored for sales reps to prep before a call.

### 💅 Apple-style Glassmorphism UI

Frosted glass cards (bg-white/60 backdrop-blur-xl)

Minimal gradients & depth shadows

Responsive design

Dark/light contrast support

### 🧩 Scalable Modular Backend

Each feature = separate route → easy to extend.

Common prompt + HTTP logic reusable across modules.

⚡ Performance

Async FastAPI calls (non-blocking)

Ollama local inference (< 3–6s per request)

Minimal network latency (loopback API)

## 🧪 Testing
### 🧱 Backend Testing

#### Manual tests:

curl -X POST http://127.0.0.1:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text":"Ollama makes local models easy","bullets":5}'


Unit tests (optional setup):

Add pytest to backend venv:

pip install pytest
pytest -v


Write route-level tests under backend/tests/.

### 🌐 Frontend Testing

Manual:

Run:

npm run dev


Open http://localhost:5173.

Functional:

Test each page:

Paste text → check /api/summarize response.

Enter company URL → verify /api/company/summary.

Upload PDF → verify /api/prospect/upload.

Fill report → check /api/report/precall.

## 🔄 Development Workflow
Step	Command
Start Ollama	ollama serve
Run Backend	cd backend && uvicorn app.main:app --reload --port 8000
Run Frontend	cd frontend && npm run dev
Test Ollama API	curl http://127.0.0.1:11434/api/version


## 🧭 Future Roadmap
### Milestone	Description
History & Persistence	Save generated reports in Postgres; fetch & view past research.
Cache Layer	Add Redis to avoid redundant LLM calls.
Vector DB (RAG)	Store embeddings for semantic search across companies/prospects.
Streaming UI	Implement SSE-based streaming for token-by-token output.
Export to PDF	Generate branded, printable PDF reports.
Authentication	Add user login for team-based use.
🛠️ Local Setup Summary
# 1. Install Ollama and Llama3 model
brew install ollama
ollama pull llama3:8b

# 2. Backend setup
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Frontend setup
cd ../frontend
npm install
npm run dev

# 4. Test full flow
ollama serve  # in separate terminal
open http://localhost:5173

## 🧠 Query Flow Summary
### User input → React Form → FastAPI Route → Clean/Parse → Build Prompt →
### → HTTP request to Ollama → Llama3 generates → FastAPI sends back JSON →
### → React renders Markdown result in glass card

##🏁 Summary

Sales Copilot is a full-stack demonstration of a local Generative AI product —
it’s private, fast, and modular, showing mastery of frontend, backend, and LLM orchestration.
This project can easily evolve into a production SaaS or enterprise-ready tool with minor scaling improvements.

