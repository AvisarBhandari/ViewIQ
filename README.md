# ViewIQ

> Paste one YouTube URL or up to four and chat with an AI that has read every word of the transcripts and knows the real engagement numbers.

**Live:** [Live Demo](https://rag-chatbot-six-zeta.vercel.app/)

---

## What it does

ViewIQ ingests YouTube videos and lets you have a grounded conversation about them. The AI has access to the full transcript of each video plus its actual metadata views, likes, comments, engagement rate, duration, upload date, and subscriber count so answers are backed by real data, not hallucinations.

**Single-video mode** — deep-dive into one video: content summary, hook breakdown, engagement analysis, improvement suggestions.

**Comparison mode** — load up to 4 videos side by side and ask the AI to compare hooks, engagement rates, creator style, or anything else across them.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Vector store | ChromaDB (persistent) |
| Embeddings | NVIDIA Llama Nemotron via OpenRouter |
| LLM | GPT-OSS 120B via OpenRouter (streaming) |
| Transcripts | Supadata API → youtube-transcript-api fallback |
| Metadata | YouTube Data API v3 |
| Frontend deploy | Vercel (Edge runtime for streaming) |
| Backend deploy | Render |
| CI/CD | GitHub Actions |

---

## How it works

```
User pastes YouTube URL(s)
         │
         ▼
  Next.js Frontend
  /api/* proxy routes
         │
    ┌────┴────┐
    ▼         ▼
 /ingest    /chat
    │         │
    ▼         ▼
FastAPI Backend (Render)
    │         │
    ├─ Supadata API      ← transcript (avoids YouTube IP blocks)
    ├─ YouTube Data API  ← views, likes, comments, duration, etc.
    ├─ OpenRouter        ← embeddings + LLM
    └─ ChromaDB          ← vector store
         │
         ▼
  Chunks stored with full metadata
         │
         ▼ (on /chat)
  retrieve_per_video() — k chunks per active video
         │
  Context block assembled:
  ┌─ Metadata (views, likes, eng. rate…)
  └─ Transcript chunks (labelled by video + chunk index)
         │
  OpenRouter LLM (streaming)
         │
  Edge route pipes tokens → browser in real time
```

---

## Project structure

```
ViewIQ/
├── backend/
│   ├── main.py                        # FastAPI app — all routes
│   ├── requirements.txt
│   ├── render.yaml                    # Render deployment config
│   └── services/
│       ├── youtube_service.py         # Transcript: Supadata → proxy fallback
│       ├── metadata_service.py        # YouTube Data API v3
│       ├── ingestion_service.py       # Ingest pipeline orchestrator
│       ├── preprocessing_service.py   # Transcript cleaning
│       ├── chunking_service.py        # Sliding-window chunker
│       ├── embedding_service.py       # OpenRouter embeddings
│       ├── vectorstore_service.py     # ChromaDB read/write (stores metadata)
│       ├── retrieval_service.py       # Per-video similarity search
│       ├── rag_service.py             # Context assembly + source metadata
│       └── llm_service.py             # Streaming, dynamic system prompt
├── frontend/
│   ├── app/
│   │   ├── page.js                    # Root — landing or chat layout
│   │   ├── layout.js
│   │   └── api/                       # Next.js proxy routes
│   │       ├── chat/route.js          # Edge runtime — real-time streaming
│   │       ├── ingest/route.js
│   │       ├── ingest-one/route.js
│   │       ├── remove/[video_id]/route.js
│   │       └── clear/route.js
│   ├── components/
│   │   ├── UrlForm.jsx                # Landing page (1 or 2 URLs to start)
│   │   ├── VideoGrid.jsx              # Sidebar: cards, add/remove, stats
│   │   └── ChatRoom.jsx               # Streaming chat UI
│   └── lib/
│       └── api.js                     # Axios instance (relative /api/* URLs)
├── .github/workflows/ci-cd.yml        # Lint → build → deploy on push to main
└── vercel.json
```

---

## Getting started

### Prerequisites

- Node.js 20+
- Python 3.11+
- API keys — see Environment variables below

### 1. Clone

```bash
git clone https://github.com/AvisarBhandari/ViewIQ.git
cd ViewIQ
```

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
uvicorn main:app --reload
# → http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
BACKEND_URL=http://localhost:8000
```

```bash
npm run dev
# → http://localhost:3000
```

---

## Environment variables

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | [openrouter.ai](https://openrouter.ai) — used for both embeddings and LLM |
| `YOUTUBE_API_KEY` | ✅ | Google Cloud Console → YouTube Data API v3 |
| `SUPADATA_API_KEY` | ✅ | [supadata.ai](https://supadata.ai) — transcript API, free tier 1000 req/mo |
| `FRONTEND_URL` | ✅ | CORS origin — `http://localhost:3000` locally, your Vercel URL in prod |
| `EMBEDDING_MODEL` | optional | Defaults to `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| `EMBEDDING_API_URL` | optional | Defaults to `https://openrouter.ai/api/v1/embeddings` |

### Frontend — `frontend/.env.local`

| Variable | Required | Description |
|---|---|---|
| `BACKEND_URL` | ✅ | Backend URL — server-side only |

> All API calls go through Next.js proxy routes (`/api/*`) so the backend URL is never exposed to the browser.

---

## Deployment

### Backend → Render

`backend/render.yaml` is included. Connect the repo to Render, set root directory to `backend`, and add all env vars in the Render dashboard.

```
Build:  pip install --upgrade pip && pip install -r requirements.txt
Start:  uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend → Vercel

Import the repo on Vercel. `vercel.json` handles the monorepo layout. Add one environment variable:

```
BACKEND_URL = https://your-app.onrender.com
```

> The chat route uses `export const runtime = "edge"` so tokens stream to the browser in real time instead of being buffered and dropped all at once — this is required on Vercel.

### CI/CD — GitHub Actions

`.github/workflows/ci-cd.yml` runs on every push to `main`:

1. Flake8 lints the backend
2. Builds the Next.js frontend
3. Deploys to Vercel
4. Triggers the Render deploy hook

Required GitHub secrets:

| Secret | Where to get it |
|---|---|
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens |
| `VERCEL_ORG_ID` | `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | `.vercel/project.json` after `vercel link` |
| `RENDER_DEPLOY_HOOK_URL` | Render → your service → Settings → Deploy Hook |

---

## Features

- Start with 1 video or 2, add more mid-session up to a limit of 4
- Remove individual videos without resetting the whole session
- Engagement stats visible on each card and passed to the model as context
- Streaming responses with a stop button tokens arrive in real time on both localhost and Vercel
- Source citations on every answer showing which video and chunk each claim came from
- Suggestions adapt to single-video vs comparison mode
- "Clear session" wipes the vector store and returns to the landing page
- Dark mode following system preference

---

## Known limitations

- Videos with transcripts disabled on YouTube will always fail no API can retrieve them.
- ChromaDB stores data on disk on the Render server. The free tier does not persist storage across deploys, so the vector store is wiped on redeploy. Each session is ephemeral by design.
- The free Render tier spins down after inactivity the first request after sleep can take 30–60 seconds.
- YouTube Data API has a 10,000 unit/day free quota. Each video ingestion uses approximately 3 units.

---
