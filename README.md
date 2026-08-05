# 🧠 Agentic RAG Nexus

**Multi-Agent Document Intelligence with Human-in-the-Loop**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.62-purple)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red)](https://streamlit.io)

&gt; Production-ready Agentic AI system that combines **LangGraph orchestration**, **CrewAI agents**, and **Human-in-the-Loop approval** for trustworthy document Q&A.

---

## 🎥 Demo

![Agentic RAG Nexus Demo](docs/images/demo.gif)

**Live Demo:** [Coming Soon]

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Query Analyst** | Rewrites and optimizes user queries with intent detection |
| 📚 **Document Retriever** | Semantic search via ChromaDB + HuggingFace embeddings |
| ✍️ **Answer Synthesizer** | Generates cited answers from retrieved context |
| 🛡️ **Quality Critic** | Scores answers 0-10, detects hallucinations |
| 🛑 **Human-in-the-Loop** | Approval gate before final delivery |
| ♻️ **Auto-Retry Loop** | Rejected answers automatically improve with feedback |
| 📊 **Real-time Tracker** | Live agent progress visualization |

---

## 🏗️ Architecture

┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   START     │────▶│  Query Analyst  │────▶│  Retriever  │
└─────────────┘     └─────────────────┘     └──────┬──────┘
│
┌───────────────────────┘
▼
┌─────────────┐
│ Synthesizer │
└──────┬──────┘
│
▼
┌─────────────┐
│    Critic   │◄────────────────┐
└──────┬──────┘                 │
│                        │
Score < 7   │   Score >= 7           │
┌─────────────┘                      [LOOP]
│
▼
┌───────────────┐
│  Human Gate   │  🛑 Interrupt for approval
│  (interrupt)  │
└───────┬───────┘
│
Approved │ Rejected
▼
┌───────────────┐
│  END / FINAL  │
└───────────────┘


---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Groq API Key](https://console.groq.com)
- [LangSmith API Key](https://smith.langchain.com) (optional)

### Local Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/agentic-rag-nexus.git
cd agentic-rag-nexus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python scripts/init_db.py

# Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit frontend (new terminal)
streamlit run frontend/app.py --server.port 8501

# Build and run with Docker Compose
docker-compose -f deployment/docker/docker-compose.yml up -d

# Access:
# API: http://localhost:8000/docs
# UI:  http://localhost:8501

| Method | Endpoint                    | Description                |
| ------ | --------------------------- | -------------------------- |
| POST   | `/api/v1/upload/upload`     | Upload PDF/DOCX/TXT        |
| GET    | `/api/v1/upload/documents`  | List uploaded documents    |
| POST   | `/api/v1/chat/stream`       | Streaming chat with agents |
| POST   | `/api/v1/chat/ask`          | Synchronous chat           |
| POST   | `/api/v1/chat/approve`      | Human approval/rejection   |
| GET    | `/api/v1/chat/session/{id}` | Get session state          |
| GET    | `/api/v1/health/health`     | Health check               |

| Layer             | Technology                     |
| ----------------- | ------------------------------ |
| **Orchestration** | LangGraph                      |
| **Agents**        | CrewAI-style roles             |
| **LLM**           | Groq (Llama 3.3 70B)           |
| **Embeddings**    | HuggingFace (all-MiniLM-L6-v2) |
| **Vector DB**     | ChromaDB                       |
| **Backend**       | FastAPI                        |
| **Frontend**      | Streamlit                      |
| **Database**      | SQLite (PostgreSQL ready)      |

📸 Screenshots
Agent Execution Tracker
docs/images/tracker.png
Human Approval Gate
docs/images/human-gate.png
Chat Interface
docs/images/chat.png

🌐 Deployment

railway login
railway init
railway up

AWS EC2
Launch Ubuntu 22.04 instance
Open ports 8000, 8501
Run: bash deployment/aws/ec2-setup.sh
Upload project and run docker-compose

📝 License
MIT License — feel free to use for personal and commercial projects.
🤝 Contact
Built by A.H.M. Nazmul Hasan
📧 nazmul3007@diu.edu.bd
🐙 github.com/nh30073007

