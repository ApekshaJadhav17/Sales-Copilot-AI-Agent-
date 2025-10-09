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

  sequenceDiagram
  autonumber
  participant U as User (Browser)
  participant FE as React App
  participant BE as FastAPI
  participant OL as Ollama (127.0.0.1:11434)
  participant M as Llama 3 (8B)

  U->>FE: Paste text / URL / Upload PDF
  FE->>BE: POST /api/... (JSON or multipart)
  Note over BE: Validate (Pydantic), parse (Trafilatura/pypdf), build prompt
  BE->>OL: POST /api/generate OR /api/chat (prompt, model)
  OL->>M: Run inference locally
  M-->>OL: Tokens/response
  OL-->>BE: { response: "markdown..." }
  BE-->>FE: { summary/report_md }
  FE-->>U: Render Markdown in glass card


  ## Project Structure
  sales-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py               # App entrypoint, routers & CORS
│   │   ├── routes/
│   │   │   ├── summarize.py      # /api/summarize — text summarizer
│   │   │   ├── company.py        # /api/company/summary — web crawl + summarize
│   │   │   ├── upload.py         # /api/prospect/upload — PDF → summary
│   │   │   ├── report.py         # /api/report/precall — final report generator
│   │   └── utils/ (optional)     # text cleaners, model helpers
│   ├── .env                      # env vars (OLLAMA_BASE_URL, etc.)
│   ├── requirements.txt          # backend dependencies
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx          # glassmorphism dashboard
│   │   │   ├── Summarizer.tsx
│   │   │   ├── Company.tsx
│   │   │   ├── Prospect.tsx
│   │   │   └── Report.tsx
│   │   ├── lib/api.ts            # shared axios/fetch wrapper
│   │   ├── App.tsx               # router + layout
│   │   ├── main.tsx              # entrypoint w/ QueryClientProvider
│   │   └── index.css             # Tailwind + base styles
│   ├── vite.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md (this file)


