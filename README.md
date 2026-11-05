# ExamForge — Autonomous AI Academic Examination Platform

ExamForge is an autonomous, evidence-driven academic examination platform powered by real dual-engine AI: **Google Gemini** and **IBM Granite (via watsonx.ai)**, orchestrated with **LangGraph** and grounded in curriculum documents using **ChromaDB** vector retrieval.

ExamForge is not a quiz application, chatbot, or static PDF summarizer. It acts as an astute, persistent academic examiner that deconstructs syllabi, poses targeted questions, semantically evaluates reasoning depth with IBM Granite, adapts dynamically, and compiles verified performance reports.

---

## 1. Six-Agent Real AI Architecture

ExamForge maintains a strict, non-negotiable allocation across six logical AI responsibilities:

| Agent | Responsibility | Model Provider | Key Engine Role |
| :--- | :--- | :--- | :--- |
| **Agent 1** | **Document Understanding** | Google Gemini | Extracts hierarchical modules, topics, subtopics, definitions, algorithms, and formulas. |
| **Agent 2** | **Question Generation** | Google Gemini | Authors comprehensive questions across 8 cognitive categories and 3 difficulty tiers with rubrics. |
| **Agent 3** | **Autonomous Examiner** | Google Gemini | Conducts oral examination, analyzes previous answers + Granite evaluations, and formulates adaptive follow-ups. |
| **Agent 4** | **Final Report Generation** | Google Gemini | Synthesizes overall performance, knowledge gaps, and prioritized study roadmaps from stored evidence. |
| **Agent 5** | **Answer Evaluation** | IBM Granite (watsonx.ai) | Semantically evaluates answers on 5 weighted criteria: Correctness (30%), Completeness (25%), Conceptual (20%), Reasoning (15%), Application (10%). |
| **Agent 6** | **Knowledge Assessment** | IBM Granite (watsonx.ai) | Assesses cumulative topic mastery (Strong, Partially Understood, Weak, Not Assessed) from real examination evidence. |

### Architectural Model Routing

```python
AGENT_MODEL_MAPPING = {
    "document_understanding": "gemini",
    "question_generation": "gemini",
    "examination": "gemini",
    "answer_evaluation": "granite",
    "knowledge_assessment": "granite",
    "report_generation": "gemini",
}
```

---

## 2. Examination Lifecycle Sequence

```text
STUDENT STARTS EXAMINATION
          │
          ▼
GEMINI AUTONOMOUS EXAMINER
          │
          ▼
FORMULATES INITIAL QUESTION
          │
          ▼
STUDENT SUBMITS ANSWER
          │
          ▼
PERSIST ANSWER (PostgreSQL)
          │
          ▼
REAL GRANITE ANSWER EVALUATION (watsonx.ai)
          │
          ▼
PERSIST EVALUATION (PostgreSQL)
          │
          ▼
REAL GRANITE KNOWLEDGE ASSESSMENT (watsonx.ai)
          │
          ▼
PERSIST KNOWLEDGE PROFILE (PostgreSQL)
          │
          ▼
SEND EVIDENCE TO GEMINI EXAMINER
          │
          ▼
GEMINI DECIDES NEXT ACTION (Follow-up Probe vs New Curriculum Topic)
          │
          ▼
APPLICATION VALIDATES CONSTRAINTS & LIMITS
          │
          ├─────────────────────────┬─────────────────────────┐
          ▼                         ▼                         ▼
   FOLLOW-UP QUESTION         NEW QUESTION           COMPLETION CRITERIA MET
          │                         │                         │
          └────────────┬────────────┘                         ▼
                       │                             GEMINI REPORT GENERATION
                       ▼                                      │
                STUDENT ANSWERS                               ▼
                       │                             PERSIST FINAL REPORT
                 (Repeat Cycle)                               │
                                                              ▼
                                                     AUTHENTICATED PDF EXPORT
```

---

## 3. Technology Stack

- **Backend Framework:** FastAPI (Python 3.10+)
- **Relational Database & ORM:** PostgreSQL 15+ & SQLAlchemy 2.0
- **Database Migrations:** Alembic
- **Agent Orchestration:** LangGraph (StateGraph with PostgreSQL-backed persistence)
- **Vector Storage & Semantic RAG:** ChromaDB & local Sentence Transformers (`all-MiniLM-L6-v2`)
- **PDF & Document Processing:** PyMuPDF & Tesseract OCR fallback
- **Report Generation & Export:** ReportLab PDF Generation
- **Frontend Framework:** React 18 & Vite
- **Styling & Design System:** Tailwind CSS (Ivory, Cream, Sand, Terracotta, Sage palette)
- **Data Visualizations:** Recharts & Lucide React
- **Containerization:** Docker & Docker Compose

---

## 4. Repository Structure

```text
ExamForge/
├── backend/
│   ├── alembic/              # Database migration environment & versions
│   │   ├── versions/         # Alembic migration scripts
│   │   └── env.py            # Migration runtime (synchronized with settings)
│   ├── app/
│   │   ├── agents/           # Six dedicated AI agent modules
│   │   │   ├── document_understanding.py  # Agent 1 (Gemini)
│   │   │   ├── question_generation.py     # Agent 2 (Gemini)
│   │   │   ├── examination_agent.py       # Agent 3 (Gemini)
│   │   │   ├── report_generation.py       # Agent 4 (Gemini)
│   │   │   ├── answer_evaluation.py       # Agent 5 (Granite)
│   │   │   └── knowledge_assessment.py    # Agent 6 (Granite)
│   │   ├── api/              # FastAPI REST endpoints
│   │   │   ├── auth.py       # Authentication & JWT
│   │   │   ├── documents.py  # PDF upload, status, knowledge map
│   │   │   ├── examinations.py # Examination sessions & submissions
│   │   │   ├── questions.py  # Question bank repository
│   │   │   ├── reports.py    # Report synthesis & PDF downloads
│   │   │   ├── knowledge.py  # Cumulative knowledge profiles
│   │   │   └── settings.py   # System & AI provider health checks
│   │   ├── core/             # Configuration, security, dependencies
│   │   ├── database/         # Connection engine & 14 SQLAlchemy models
│   │   ├── llm/              # Live Gemini and Granite clients & router
│   │   ├── prompts/          # Six prompt modules for each agent responsibility
│   │   ├── schemas/          # Pydantic request & response schemas
│   │   ├── services/         # PDF, embedding, examination & report services
│   │   ├── workflows/        # LangGraph StateGraph, nodes & checkpoints
│   │   └── tests/            # Automated pytest suite
│   ├── alembic.ini
│   ├── Dockerfile            # Production backend container build
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/layout/ # Main application layout & navigation
│   │   ├── pages/            # All 11 dedicated frontend experiences
│   │   │   ├── LandingPage.jsx         # Page 1: Product overview & architecture
│   │   │   ├── LoginPage.jsx           # Page 2: Student login
│   │   │   ├── RegisterPage.jsx        # Page 2: Student registration
│   │   │   ├── DashboardPage.jsx       # Page 3: Central dashboard & resume
│   │   │   ├── DocumentsPage.jsx       # Page 4: Document upload & tracking
│   │   │   ├── DocumentDetailPage.jsx  # Page 5: Hierarchical knowledge map
│   │   │   ├── QuestionBankPage.jsx    # Page 6: Grounded question bank
│   │   │   ├── ExamSessionPage.jsx     # Page 7: Examination room
│   │   │   ├── ExaminationsPage.jsx    # Page 8: Examination history
│   │   │   ├── KnowledgePage.jsx       # Page 9: Topic mastery profiling
│   │   │   ├── ReportDetailPage.jsx    # Page 10: Academic report & PDF export
│   │   │   ├── ReportsPage.jsx         # Page 10: Report library
│   │   │   └── SettingsPage.jsx        # Page 11: AI provider & system status
│   │   ├── services/api.js   # Centralized Axios client with Bearer auth
│   │   ├── store/authStore.js# Zustand auth token persistence
│   │   ├── App.jsx           # React Router route declarations
│   │   └── index.css         # Custom tokens & typography styling
│   ├── Dockerfile            # Frontend container build
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── storage/
│   ├── uploads/              # Uploaded PDF files
│   └── chroma/               # ChromaDB vector index
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Prerequisites

Before running ExamForge on Windows, ensure the following tools are installed:

- **Python 3.10 or 3.11** (`python --version`)
- **Node.js 20+** (`node -v`, `npm -v`)
- **PostgreSQL 15+** (running locally on port 5432 or via Docker)
- **Tesseract OCR** (optional, recommended for scanned PDF support)
- **PowerShell 5.1+ or PowerShell 7+**

---

## 6. Environment Configuration

Copy `.env.example` in the project root to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your actual credentials:

```env
# ── AI Provider Mode (Strict Live Inference) ──────────────────────────────────
AI_PROVIDER_MODE=live

# ── Google Gemini Configuration ───────────────────────────────────────────────
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL_ID=gemini-1.5-flash

# ── IBM watsonx.ai Granite Configuration ──────────────────────────────────────
WATSONX_API_KEY=your_actual_watsonx_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2

# ── Database Connection ───────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/examforge

# ── Security & Storage ────────────────────────────────────────────────────────
JWT_SECRET_KEY=super-secure-random-secret-key-for-jwt-tokens
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=storage/uploads
CHROMA_DIR=storage/chroma
```

> [!NOTE]
> If live AI credentials are not yet configured, the non-AI infrastructure (Auth, Document management, Database, Navigation) will run normally, while AI operations will clearly display the missing configuration error rather than fabricating fake outputs.

---

## 7. Windows PowerShell Setup & Startup

### Step 1: Python Virtual Environment & Dependencies

Open PowerShell in the `ExamForge` root:

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Step 2: Database Setup & Alembic Migrations

Ensure your PostgreSQL instance is running, then execute migrations:

```powershell
# Apply database migrations
alembic upgrade head
```

### Step 3: Run Backend Server

```powershell
# Start FastAPI backend server with reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- API Base: `http://localhost:8000/api`
- Interactive Swagger Documentation: `http://localhost:8000/docs`

---

### Step 4: Frontend Setup & Startup

Open a second PowerShell window:

```powershell
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser at:
`http://localhost:5173`

---

## 8. Docker Compose Deployment (Alternative Full-Stack)

To spin up the entire application including PostgreSQL, FastAPI, and Vite in containers:

```powershell
# Start all services with volume persistence
docker compose up --build -d

# View service logs
docker compose logs -f

# Stop all services
docker compose down
```

---

## 9. Running Automated Tests

To run the backend test suite:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest app/tests/ -v
```

To run a frontend production build check:

```powershell
cd frontend
npm run build
```

---

## 10. Provider Connectivity Verification

You can verify your live AI connections directly from the UI or API:

1. Log into ExamForge.
2. Navigate to **Settings & Status** (`/settings`).
3. Click **"Verify Live AI Connections"**.
4. ExamForge will ping both Google Gemini and IBM Granite with verification probes and report live model status without exposing private keys.

---

## 11. Troubleshooting

- **PostgreSQL Connection Error (`ConnectionRefusedError`):**
  Verify that your PostgreSQL service is running (`Get-Service postgres*`) and that the credentials in `DATABASE_URL` match your local PostgreSQL user/password.
- **Tesseract OCR Warning:**
  If Tesseract is not installed on Windows, digital PDFs will still extract 100% via PyMuPDF. For scanned pages, install Tesseract from UB-Mannheim and ensure it is in your Windows PATH.
- **Alembic `Target database is not up to date`:**
  Run `alembic upgrade head` from the `backend/` directory.
- **Port Conflicts (8000 or 5173 in use):**
  Identify and release the process using `Get-NetTCPConnection -LocalPort 8000` or change the port flags in the startup command.
