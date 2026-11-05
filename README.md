# ExamForge

An autonomous AI examination platform that ingests academic documents, generates adaptive multi-category questions, conducts Socratic-style oral examinations, evaluates free-text answers, and produces detailed knowledge-profile reports.

---

## Architecture Overview

```
ExamForge/
├── backend/          FastAPI + SQLAlchemy + LangGraph
├── frontend/         React + Vite + Tailwind CSS
├── storage/
│   ├── uploads/      PDF uploads
│   └── chroma/       ChromaDB vector store
└── docs/
```

### AI Stack
- **Document understanding** — Gemini Flash (or IBM Granite via Watsonx)
- **Question generation** — Gemini Pro / Granite
- **Answer evaluation** — Gemini Pro / Granite
- **Report generation** — Gemini Pro / Granite
- **Embeddings** — `sentence-transformers` (local, free)
- **Vector store** — ChromaDB (local)
- **Orchestration** — LangGraph stateful graphs

Set `AI_PROVIDER_MODE=mock` in `.env` to run fully offline with canned responses.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| PostgreSQL | 15+ |
| Tesseract OCR | 5+ |

---

## Local Setup

### 1. Clone & configure environment

```bash
git clone https://github.com/your-org/examforge.git
cd examforge
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and JWT_SECRET_KEY
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at http://localhost:5173

---

## Docker Compose (recommended for full stack)

```bash
docker compose up --build
```

Services:
- **db** — PostgreSQL 15 on port 5432
- **backend** — FastAPI on port 8000
- **frontend** — Vite dev server on port 5173

---

## Running with real AI providers

### Gemini (Google AI Studio)
1. Get a free API key at https://aistudio.google.com/app/apikey
2. Set `GEMINI_API_KEY=your-key` and `AI_PROVIDER_MODE=live` in `.env`

### IBM Watsonx / Granite
1. Create a project at https://cloud.ibm.com/watsonx
2. Set `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_URL` in `.env`
3. Set `AI_PROVIDER_MODE=live`

---

## Running Tests

```bash
cd backend
pytest app/tests/ -v
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/examforge` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | *(must set)* | Secret for signing JWTs |
| `AI_PROVIDER_MODE` | `mock` | `mock` or `live` |
| `GEMINI_API_KEY` | `` | Google Gemini API key |
| `WATSONX_API_KEY` | `` | IBM Watsonx API key |
| `WATSONX_PROJECT_ID` | `` | IBM Watsonx project ID |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` | Watsonx endpoint |
| `GRANITE_MODEL_ID` | `ibm/granite-13b-instruct-v2` | Granite model ID |
| `MAX_FILE_SIZE_MB` | `50` | Max PDF upload size |
| `UPLOAD_DIR` | `storage/uploads` | Upload storage path |
| `CHROMA_DIR` | `storage/chroma` | ChromaDB storage path |
