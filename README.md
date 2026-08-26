# 🧠 Agentic RAG Nexus

### Multi-Agent Document Intelligence with Human-in-the-Loop

A production-oriented **Agentic RAG (Retrieval-Augmented Generation) system** for intelligent document analysis, question answering, and quality-controlled AI responses.

Agentic RAG Nexus combines **LangGraph-based orchestration**, semantic document retrieval, local embeddings, and **Human-in-the-Loop review** to create a transparent and extensible document intelligence pipeline.

---






## 🚀 Overview

Traditional RAG applications usually follow a simple pipeline:

```text
User Query
    ↓
Retrieve Documents
    ↓
LLM Response

Agentic RAG Nexus extends this workflow into a structured multi-stage reasoning pipeline:

User Query
    ↓
Query Analysis
    ↓
Document Retrieval
    ↓
Answer Synthesis
    ↓
Quality Critique
    ↓
Human Review (if required)
    ↓
Final Response











The system is designed with a focus on:

Modular AI architecture
Agent orchestration
Semantic document retrieval
Answer quality evaluation
Human oversight
Local LLM compatibility
API-first backend design
Cloud-deployable frontend and backend
✨ Features
Feature	Description
🔍 Query Analyzer	Processes and prepares user queries for downstream retrieval
📚 Semantic Retrieval	Retrieves relevant document chunks using vector similarity search
🧠 Agent Orchestration	Coordinates the AI workflow using LangGraph
✍️ Answer Synthesizer	Generates answers from retrieved document context
🛡️ Quality Critic	Evaluates generated responses and assigns a quality score
🧑‍💻 Human-in-the-Loop	Allows human approval or rejection for low-confidence responses
♻️ Feedback Loop	Rejected responses can be regenerated using reviewer feedback
📄 Multi-Document Support	Supports PDF, DOCX, TXT, and Markdown files
📊 Agent Pipeline Tracker	Displays the execution state of individual agents
💬 Conversation History	Stores and retrieves chat sessions
🗄️ Vector Database	Uses ChromaDB for document embeddings and similarity search
🔌 API-First Design	FastAPI backend with structured REST endpoints
🤖 Local LLM Support	Designed to work with Ollama-hosted models such as Phi-3 or Llama















🏗️ System Architecture
                         ┌──────────────────────┐
                         │       USER           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │    STREAMLIT FRONTEND       │
                    │                             │
                    │  • Document Upload          │
                    │  • Chat Interface           │
                    │  • Agent Status Tracker     │
                    │  • Human Approval UI        │
                    └──────────────┬──────────────┘
                                   │ REST API
                                   ▼
                    ┌─────────────────────────────┐
                    │      FASTAPI BACKEND        │
                    │                             │
                    │  • Upload API               │
                    │  • Chat API                 │
                    │  • Session Management       │
                    │  • Health Monitoring        │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       LANGGRAPH             │
                    │    AGENT ORCHESTRATION      │
                    └──────────────┬──────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ QUERY ANALYZER  │──────▶│ DOCUMENT        │──────▶│ ANSWER          │
│                 │       │ RETRIEVER       │       │ SYNTHESIZER     │
└─────────────────┘       └────────┬────────┘       └────────┬────────┘
                                   │                         │
                                   ▼                         ▼
                           ┌───────────────┐         ┌─────────────────┐
                           │   CHROMADB    │         │ QUALITY CRITIC  │
                           │ VECTOR STORE  │         └────────┬────────┘
                           └───────────────┘                  │
                                                              ▼
                                                     ┌─────────────────┐
                                                     │ QUALITY SCORE   │
                                                     └────────┬────────┘
                                                              │
                                      ┌───────────────────────┴───────────────────────┐
                                      │                                               │
                                      ▼                                               ▼

                               Score Accepted                                  Score Requires Review
                                      │                                               │
                                      ▼                                               ▼

                               ┌─────────────┐                            ┌─────────────────────┐
                               │ FINAL ANSWER│                            │ HUMAN REVIEW GATE   │
                               └─────────────┘                            └──────────┬──────────┘
                                                                                     │
                                                                     ┌───────────────┴───────────────┐
                                                                     │                               │
                                                                     ▼                               ▼

                                                                 APPROVED                        REJECTED
                                                                     │                               │
                                                                     ▼                               ▼

                                                               FINAL ANSWER                  FEEDBACK LOOP
                                                                                                     │
                                                                                                     └──────▶ Retry Pipeline













🧩 Agent Pipeline

The system uses a structured multi-agent workflow.

1. Query Analyzer

The Query Analyzer processes the incoming user query and prepares it for retrieval.

Responsibilities:

Understand user intent
Normalize the query
Improve retrieval relevance
Prepare the query for downstream agents
User Query
    ↓
Query Analyzer
    ↓
Processed Query





2. Document Retriever

The Retriever performs semantic search against the document collection.

Pipeline:

Document
    ↓
Chunking
    ↓
FastEmbed Embeddings
    ↓
ChromaDB
    ↓
Similarity Search
    ↓
Relevant Context



Supported document formats:

PDF
DOCX
TXT
Markdown






3. Answer Synthesizer

The Answer Synthesizer receives:

Processed Query
+
Retrieved Context

It generates a context-aware answer using the configured LLM provider.

The system is designed primarily for local inference through Ollama.

Supported examples:

Phi-3
Llama 3.1
Other Ollama-compatible models
4. Quality Critic

The Critic evaluates the generated answer.

Example evaluation areas:

Relevance
Context grounding
Answer completeness
Response quality
Potential hallucination risk

The Critic produces a quality score.


Answer
   ↓
Quality Critic
   ↓
Score
5. Human-in-the-Loop Review

When an answer requires additional review, the system activates a human approval gate.






AI Generated Answer
        ↓
Human Review
        ↓
 ┌───────────────┐
 │               │
 ▼               ▼

Approve          Reject
 │               │
 ▼               ▼

Final          Feedback
Answer           ↓
              Retry






This provides an additional layer of control for AI-generated responses.

🛠️ Technology Stack
Layer	Technology
Language	Python 3.11
Backend	FastAPI
Frontend	Streamlit
Agent Orchestration	LangGraph
LLM Integration	LangChain + Ollama
Local LLM	Ollama
Embeddings	FastEmbed
Vector Database	ChromaDB
Database	SQLite
ORM	SQLAlchemy
Async Database	aiosqlite
Document Parsing	PyPDF + python-docx
API Validation	Pydantic
Deployment	Render + Streamlit Cloud
Logging	Structlog










📂 Project Structure
agentic-rag-nexus/
│
├── app/
│   │
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── upload.py
│   │       └── health.py
│   │
│   ├── agents/
│   │   ├── analyzer.py
│   │   ├── retriever.py
│   │   ├── synthesizer.py
│   │   └── critic.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── embedding_service.py
│   │   └── document_service.py
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── graph/
│   │   └── agent_graph.py
│   │
│   └── main.py
│
├── frontend/
│   │
│   ├── app.py
│   │
│   ├── components/
│   │   └── sidebar.py
│   │
│   └── utils/
│       └── api_client.py
│
├── scripts/
│   └── init_db.py
│
├── deployment/
│   └── docker/
│
├── docs/
│   └── images/
│
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md










⚙️ Local Development
Prerequisites

Make sure you have:

Python 3.11+
Ollama installed
A supported Ollama model

Example:

ollama pull phi3

Or:

ollama pull llama3.1
1. Clone the Repository
git clone <YOUR_REPOSITORY_URL>
cd agentic-rag-nexus
2. Create a Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / macOS
python -m venv venv
source venv/bin/activate
3. Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt






4. Configure Environment Variables

Create a .env file:

ENVIRONMENT=development

OLLAMA_MODEL=phi3
OLLAMA_BASE_URL=http://localhost:11434

OLLAMA_TIMEOUT=300
OLLAMA_NUM_PREDICT=512
OLLAMA_TEMPERATURE=0.3

DATABASE_URL=sqlite:///./agentic_rag.db

For Llama 3.1:

OLLAMA_MODEL=llama3.1


5. Start Ollama

Make sure the Ollama service is running locally.

Example:

ollama run phi3

Or:

ollama run llama3.1


6. Initialize the Database
python scripts/init_db.py



7. Start the FastAPI Backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Backend:

http://localhost:8000

API documentation:

http://localhost:8000/docs

Health check:

http://localhost:8000/api/v1/health





8. Start the Streamlit Frontend

Open a new terminal:

streamlit run frontend/app.py --server.port 8501

Frontend:

http://localhost:8501
📡 API Endpoints
Health
GET /api/v1/health

Example response:

{
  "status": "healthy"
}
Upload Document
POST /api/v1/upload/upload

Supported files:

PDF
DOCX
TXT
MD
Clear Documents
POST /api/v1/upload/clear

Example request:

{
  "collection_name": "documents"
}
Collection Statistics
GET /api/v1/upload/collection/stats
Ask Question
POST /api/v1/chat/ask

Example:

{
  "query": "What are the main skills mentioned in this resume?",
  "session_id": "sess_example",
  "collection_name": "documents"
}
Streaming Chat
POST /api/v1/chat/stream
Human Approval
POST /api/v1/chat/approve

Example:

{
  "session_id": "sess_example",
  "decision": "approved",
  "feedback": "Answer looks correct."
}








Conversation History
GET /api/v1/chat/conversations
🌐 Deployment Architecture






The project separates the frontend and backend services.

                    INTERNET
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼

 ┌──────────────────┐       ┌──────────────────┐
 │ Streamlit Cloud  │──────▶│ Render           │
 │                  │ REST  │ FastAPI Backend  │
 │ Frontend         │ API   │                  │
 └──────────────────┘       └────────┬─────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼

               ChromaDB         SQLite          FastEmbed




🤖 Local LLM Architecture

The project supports local LLM inference through Ollama.

During local development:

FastAPI
   │
   ▼
Ollama
   │
   ▼
Local Model

Example:

FastAPI
   ↓
Ollama
   ↓
Phi-3

or:

FastAPI
   ↓
Ollama
   ↓
Llama 3.1







This architecture allows the project to run without requiring a paid LLM API for local development.

⚠️ Cloud Deployment Note

The backend can be deployed independently from the frontend.

However, a cloud-hosted backend cannot automatically access an Ollama instance running on a local development machine through:

http://localhost:11434

For this reason, the project architecture separates:

Cloud API / RAG Infrastructure

from:

Local / Self-hosted LLM Inference

This makes the system flexible for different deployment environments.



🔄 Agent Workflow
                USER QUESTION
                       │
                       ▼
              ┌────────────────┐
              │ QUERY ANALYZER │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │   RETRIEVER    │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │   SYNTHESIZER  │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │     CRITIC     │
              └───────┬────────┘
                      │
               ┌──────┴──────┐
               │             │
               ▼             ▼

           ACCEPTED      REVIEW REQUIRED
               │             │
               │             ▼
               │       HUMAN APPROVAL
               │             │
               │       ┌─────┴─────┐
               │       │           │
               │       ▼           ▼

               │    APPROVED    REJECTED
               │       │           │
               ▼       ▼           ▼

            FINAL RESPONSE    FEEDBACK LOOP
                                  │
                                  └──────▶ PIPELINE RETRY










📊 Current Capabilities
 FastAPI backend
 Streamlit frontend
 Document upload
 PDF processing
 DOCX processing
 TXT processing
 Markdown processing
 FastEmbed embeddings
 ChromaDB vector storage
 Semantic retrieval
 LangGraph orchestration
 Multi-stage agent workflow
 Answer quality scoring
 Human approval gate
 Conversation history
 SQLite persistence
 Render backend deployment
 Streamlit Cloud frontend deployment
 Local Ollama integration







🔮 Future Improvements



Planned improvements include:

 Persistent cloud storage for vector data
 PostgreSQL production configuration
 Authentication and user accounts
 Multi-user document isolation
 Redis-backed caching
 Background document processing
 Streaming responses in the frontend
 Docker Compose production setup
 CI/CD pipeline
 Automated tests
 Evaluation dataset
 Agent observability dashboard
 Self-hosted GPU inference support
 Role-based access control




 
🧪 Example Use Cases
Resume Analysis

Upload a resume and ask:

What are the candidate's strongest technical skills?
Research Paper Analysis

Upload a research paper and ask:

What is the main research contribution of this paper?
Document Summarization
Summarize the key findings from this document.
Knowledge Extraction
Extract the most important technical concepts from this document.




🎯 Engineering Principles

Agentic RAG Nexus is designed around several engineering principles:

Modular Architecture

Each major responsibility is separated into independent components.

API
Agents
Services
Database
Frontend
API-First Design

The backend exposes structured REST endpoints so the frontend can be replaced or extended independently.

Local-First AI

The system supports local LLM inference through Ollama, reducing dependency on external AI APIs during development.

Human Oversight

Low-confidence or review-required responses can be routed through a Human-in-the-Loop approval process.

Extensibility

The architecture can be extended with:

Alternative LLM providers
Different vector databases
PostgreSQL
Redis
Authentication
Cloud inference
GPU inference servers
🧑‍💻 Author

A.H.M. Nazmul Hasan

AI / Machine Learning Engineer

Focused on:

Agentic AI Systems
Retrieval-Augmented Generation
Local LLM Infrastructure
Multi-Agent Workflows
FastAPI Backend Development
AI Application Engineering



GitHub: nh30073007

linkedin.com/in/nazmul-hasan

Email: nazmul3007@diu.edu.bd

📄 License

This project is licensed under the MIT License.

You are free to use, modify, and distribute this project according to the terms of the license.

⭐ Project Status
Status: Active Development

Agentic RAG Nexus is an evolving portfolio and research project focused on exploring reliable architectures for:

Agentic AI
+
RAG
+
Local LLMs
+
Human Oversight