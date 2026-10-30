# KnowledgeVault AI — Deployment & Operations Guide

## 1. Deploying to Render (Recommended Cloud Deployment)

KnowledgeVault AI is optimized for [Render](https://render.com) using a unified, multi-stage production Docker container. Render automatically builds the React frontend, sets up Python 3.11 with all retrieval engines, mounts persistent storage, and runs FastAPI with zero extra configuration.

### Option A: Automatic 1-Click Blueprint (Easiest)

1. **Push your code to GitHub**:
   Ensure `Dockerfile` and `render.yaml` are committed in your GitHub repository.
   ```bash
   git add .
   git commit -m "Add Render configuration and Dockerfile"
   git push origin main
   ```

2. **Deploy on Render**:
   - Log in to [Render Dashboard](https://dashboard.render.com).
   - Click the **New +** button in the top right and select **Blueprint**.
   - Connect your GitHub repository.
   - Render will detect `render.yaml` and configure the Web Service, health checks, and persistent disk automatically.
   - Click **Apply**.

---

### Option B: Manual Web Service Setup on Render

If you prefer to configure the service manually via the Render UI:

1. In the Render Dashboard, click **New +** ➔ **Web Service**.
2. Connect your GitHub repository (`KNOWLEDGEVAULT AI`).
3. Fill in the following fields:
   - **Name**: `knowledgevault-ai`
   - **Region**: Any (e.g. `Oregon (US West)` or `Frankfurt (EU)`)
   - **Branch**: `main`
   - **Language / Runtime**: **Docker** (Render detects the root `Dockerfile` automatically)
   - **Dockerfile Path**: `./Dockerfile`
   - **Plan**: Free or Starter ($7/mo recommended if using persistent disk)
4. Under **Advanced** ➔ **Health Check Path**:
   - Set to `/health`
5. Under **Environment Variables**:
   Add the following keys:
   | Key | Default Value | Notes |
   | :--- | :--- | :--- |
   | `PORT` | `10000` | Render injects this automatically |
   | `LLM_PROVIDER` | `mock` | Change to `openai`, `anthropic`, or `gemini` if using external LLMs |
   | `OPENAI_API_KEY` | *(your key)* | Optional: Required only if `LLM_PROVIDER=openai` |
   | `ANTHROPIC_API_KEY` | *(your key)* | Optional: Required only if `LLM_PROVIDER=anthropic` |
   | `GEMINI_API_KEY` | *(your key)* | Optional: Required only if `LLM_PROVIDER=gemini` |
   | `CHUNK_SIZE` | `700` | Sliding window tokens |
   | `TOP_K` | `5` | Retrieved passages |
6. Under **Disks** (optional, recommended on Starter plan):
   - **Name**: `vault-data`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB
   *(On the Free plan, Render does not support disks; uploads remain in container storage until the free instance sleeps or restarts).*
7. Click **Create Web Service**.

Once deployed, Render provides an SSL-secured live URL:
`https://knowledgevault-ai.onrender.com`

---

## 2. Quick Local Development (Zero Docker Required)

KnowledgeVault AI is designed to run locally with zero mandatory external daemons by defaulting to SQLite (with WAL mode and foreign key enforcement) and embedded persistent vector storage.

### Prerequisites
- Python 3.11+
- Node.js 20+ & npm

### Setup Steps

1. **Clone & Configure Environment**:
   ```bash
   cp .env.example .env
   ```

2. **Backend Setup**:
   ```bash
   # Create virtualenv and install dependencies
   python -m venv backend/.venv
   # Windows:
   backend\.venv\Scripts\activate
   # Linux/macOS:
   source backend/.venv/bin/activate

   pip install -r backend/requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Start the Application**:
   ```bash
   # From root directory:
   python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
   ```
   Open your browser to: **http://127.0.0.1:8000** (serves both the React frontend and REST API).

---

## 3. Docker Compose Deployment (Self-Hosted Staging / Production)

For multi-container deployments utilizing standalone PostgreSQL 16 and a dedicated Qdrant vector database cluster:

```bash
# Build and start all services in detached mode
docker-compose up -d --build
```

### Services Started:
- `backend`: FastAPI running on port 8000
- `frontend`: Nginx serving static assets on port 3000
- `postgres`: PostgreSQL 16 on port 5432
- `qdrant`: Vector database on port 6333

---

## 4. Production Health & Observability

- **Health Check Endpoint**: `GET /health`
- **Swagger / OpenAPI Documentation**: `GET /docs`
- **Metrics Evaluator**: In-app **Benchmarks** tab or `python scripts/e2e_verification.py`
