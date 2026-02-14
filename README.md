# AI RAG Sentiment Bot

An AI-powered Retrieval-Augmented Generation (RAG) Sentiment Analysis Bot that analyzes customer sentiment, routes conversations, manages support tickets, and generates intelligent responses using LLM integration.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Architecture Overview](#architecture-overview)
4. [API Documentation](#api-documentation)
5. [System Flow](#system-flow)
6. [Environment Setup](#environment-setup)
7. [Database Schema](#database-schema)
8. [Key Features](#key-features)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Qdrant (Vector DB)
- pip or conda

### Installation

```bash
# Clone repository
git clone https://github.com/Naveencodespeaks/ai-chat-bot.git
cd ai_rag_sentiment_bot

# Create virtual environment
python -m venv env

# Activate (Windows)
.\env\Scripts\activate

# Activate (Linux/Mac)
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Run Server

```bash
# Start uvicorn server (development)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Access API documentation
# Swagger UI: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
```

### Run Migrations

```bash
# Upgrade to latest schema
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

---

## 📁 Project Structure

```
ai_rag_sentiment_bot/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   │
│   ├── api/                              # API endpoints (routers)
│   │   ├── __init__.py
│   │   ├── auth.py                       # Authentication endpoints (login, register)
│   │   ├── chat.py                       # Chat/conversation endpoints
│   │   ├── health.py                     # Health check endpoints
│   │   ├── ingest.py                     # Document ingestion endpoints
│   │   ├── sentiment.py                  # Sentiment analysis endpoints
│   │   ├── tickets.py                    # Support ticket endpoints
│   │   ├── users.py                      # User management endpoints
│   │   └── secure_test.py                # RBAC test endpoints
│   │
│   ├── actions/                          # Business logic & orchestration
│   │   ├── __init__.py
│   │   ├── ai_orchestrator.py            # AI workflow orchestration
│   │   ├── audit.py                      # Audit logging
│   │   ├── engine.py                     # Core message processing engine
│   │   ├── escalation.py                 # Ticket escalation logic
│   │   ├── notifications.py              # Notification system
│   │   ├── routing.py                    # Message routing logic
│   │   ├── sla_monitor.py                # SLA monitoring & alerts
│   │   └── ticketing.py                  # Ticket creation & management
│   │
│   ├── auth/                             # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── context.py                    # User context management
│   │   ├── dependencies.py               # FastAPI dependency injection
│   │   ├── jwt.py                        # JWT token handling
│   │   └── rbac.py                       # Role-Based Access Control
│   │
│   ├── core/                             # Core utilities & configuration
│   │   ├── __init__.py
│   │   ├── config.py                     # Environment configuration
│   │   ├── constants.py                  # Application constants
│   │   ├── logging.py                    # Loguru logging setup
│   │   ├── policies.py                   # Business policies engine
│   │   ├── scheduler.py                  # Background task scheduler
│   │   └── security.py                   # Security utilities
│   │
│   ├── db/                               # Database layer
│   │   ├── __init__.py
│   │   ├── base.py                       # SQLAlchemy Base class
│   │   ├── deps.py                       # Database dependencies
│   │   ├── session.py                    # Database session management
│   │   ├── vector.py                     # Qdrant vector DB client
│   │   └── migrations/                   # Alembic migration env
│   │       └── env.py
│   │
│   ├── models/                           # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                       # Base model mixins
│   │   ├── chat_log.py                   # Chat message logs
│   │   ├── chunk.py                      # Document chunks
│   │   ├── conversation.py               # Conversations
│   │   ├── core.py                       # Core domain models
│   │   ├── department.py                 # Departments
│   │   ├── documents.py                  # Document storage
│   │   ├── enums.py                      # Enumeration types
│   │   ├── message.py                    # Messages
│   │   ├── role.py                       # User roles
│   │   ├── routing_rule.py               # Routing rules
│   │   ├── sentiment_log.py              # Sentiment analysis logs
│   │   ├── sla_policy.py                 # SLA policies
│   │   ├── ticket.py                     # Support tickets
│   │   ├── user.py                       # Users
│   │   └── user_role.py                  # User-Role assignments
│   │
│   ├── rag/                              # Retrieval-Augmented Generation
│   │   ├── __init__.py
│   │   ├── chunker.py                    # Document chunking
│   │   ├── embedding.py                  # Text embedding
│   │   ├── filters.py                    # Query filtering
│   │   ├── ingest.py                     # Document ingestion
│   │   ├── prompt_builder.py             # Prompt generation
│   │   ├── retriever.py                  # Context retrieval
│   │   └── vector_schema.py              # Vector DB schema
│   │
│   ├── llm/                              # Large Language Model integration
│   │   ├── __init__.py
│   │   ├── client.py                     # LLM API client
│   │   ├── guardrails.py                 # Response guardrails
│   │   └── promts.py                     # Prompt templates
│   │
│   ├── sentiment/                        # Sentiment analysis module
│   │   ├── __init__.py
│   │   ├── analyzer.py                   # Main sentiment analyzer
│   │   ├── rules.py                      # Sentiment rules engine
│   │   └── strategies.py                 # Analysis strategies (lexicon, pattern, statistical)
│   │
│   ├── schemas/                          # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── auth.py                       # Auth schemas
│   │   ├── chat.py                       # Chat schemas
│   │   ├── document.py                   # Document schemas
│   │   ├── sentiment.py                  # Sentiment schemas
│   │   └── ticket.py                     # Ticket schemas
│   │
│   └── logs/                             # Application logs directory
│
├── alembic/                              # Alembic database migrations
│   ├── env.py
│   ├── script.py.mako
│   ├── README
│   └── versions/                         # Migration scripts
│       ├── 39ed6b2ef049_initial_chatbot_schema.py
│       ├── 2bcefb003bce_add_sla_and_routing_fields.py
│       ├── b1c2d3f4e567_create_tickets_table.py
│       └── a4f1d2b3c6e7_add_ticket_fields.py
│
├── scripts/                              # Utility scripts
│   ├── backfill_metadata.py              # Populate existing records
│   ├── ingest_doc.py                     # Batch document ingestion
│   └── reindex_vectors.py                # Rebuild vector indices
│
├── tests/                                # Test suite
│   ├── test_chat_flow.py                 # Chat flow tests
│   ├── test_promt_injection.py           # Security tests
│   ├── test_rbac.py                      # RBAC tests
│   └── test_sentiment.py                 # Sentiment analysis tests
│
├── docs/                                 # Documentation
│   ├── architecture.md                   # System architecture
│   ├── deployment.md                     # Deployment guide
│   ├── rbac_matrix.md                    # RBAC permissions matrix
│   └── security.md                       # Security policies
│
├── env/                                  # Python virtual environment
├── alembic.ini                           # Alembic configuration
├── docker-compose.yml                    # Docker services setup
├── pyproject.toml                        # Python project metadata
├── requirements.txt                      # Python dependencies
└── README.md                             # This file
```

---

## 🏗️ Architecture Overview

### High-Level System Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │────────▶│   FastAPI    │◀────────│  Middleware │
│  (Browser)  │         │   Server     │         │   (CORS)    │
└─────────────┘         └──────┬───────┘         └─────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼─────┐ ┌──▼──┐ ┌──────▼─────┐
              │ Auth      │ │ RAG │ │ Sentiment  │
              │ Handler   │ │     │ │ Analyzer   │
              │ (JWT/RBAC)│ │     │ │            │
              └─────┬─────┘ └──┬──┘ └──────┬─────┘
                    │          │          │
        ┌───────────┴──────────┼──────────┴────────┐
        │                      │                    │
        │          ┌───────────▼────────────┐       │
        │          │  Business Logic Engine │       │
        │          │  (orchestrator.py)     │       │
        │          └───────────┬────────────┘       │
        │                      │                    │
   ┌────▼──────┐  ┌───────────▼──────┐  ┌──────────▼──────┐
   │ PostgreSQL │  │ Qdrant Vector DB │  │  LLM Provider   │
   │ (Primary)  │  │ (RAG Context)    │  │ (OpenAI/Others) │
   └────────────┘  └──────────────────┘  └─────────────────┘
```

### Request Flow Diagram

```
HTTP Request
    │
    ▼
┌─────────────────────┐
│ FastAPI Router      │ (api/chat.py, api/sentiment.py, etc.)
└────────┬────────────┘
         │
         ▼
┌──────────────────────────┐
│ Auth Middleware          │ (auth/dependencies.py)
│ - JWT Token Validation   │
│ - RBAC Permission Check  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Request Schema Validation│ (schemas/*.py - Pydantic V2)
│ - Type checking          │
│ - Field validation       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Business Logic           │ (actions/engine.py)
│ - Process message        │
│ - Analyze sentiment      │
│ - Retrieve RAG context   │
│ - Generate response      │
└────────┬─────────────────┘
         │
    ┌────┼────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────────┐
│PostgreSQL  │ Qdrant Vector DB │
│ (store)    │ (retrieve context)│
└───────┘ └────────────┘
    │         │
    └────┬────┘
         │
         ▼
┌──────────────────────┐
│ Response Schema      │ (schemas/*.py)
│ (Pydantic model)     │
└────────┬─────────────┘
         │
         ▼
    HTTP Response
```

---

## 📡 API Documentation

### Base URL
```
http://127.0.0.1:8000/api
```

### 1️⃣ Authentication Endpoints

#### **POST /auth/login**
Login user and get JWT token.

**Input:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Output:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "roles": ["agent"]
  }
}
```

**Error Response:**
```json
{
  "detail": "Invalid credentials"
}
```

---

#### **POST /auth/register**
Register new user.

**Input:**
```json
{
  "email": "newuser@example.com",
  "password": "securepass123",
  "full_name": "Jane Smith"
}
```

**Output:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "is_active": true
}
```

---

### 2️⃣ Chat Endpoints

#### **POST /chat/message**
Send a message and get AI response.

**Input:**
```json
{
  "conversation_id": "conv-001",
  "content": "What are your business hours?",
  "context": "Customer inquiry about store hours"
}
```

**Processing Flow:**
```
1. Validate JWT token → Authorization
2. Check RBAC permissions → Access control
3. Create Message record (sender_type: USER)
4. Analyze sentiment of message → SentimentLog
5. Retrieve relevant context from Qdrant → RAG
6. Generate LLM prompt with context
7. Call LLM API (OpenAI/similar)
8. Create Message record (sender_type: BOT)
9. Return response
```

**Output:**
```json
{
  "id": "msg-12345",
  "conversation_id": "conv-001",
  "sender_type": "BOT",
  "content": "Our business hours are Monday-Friday 9 AM to 6 PM, and Saturday 10 AM to 4 PM.",
  "sentiment_score": 0.85,
  "created_at": "2026-02-14T15:30:00Z"
}
```

**Flow Diagram:**
```
POST /chat/message
        │
        ▼
    JWT Validate
        │
        ▼
    Load Conversation
        │
        ├─────────────────┬────────────────┬────────────────┐
        │                 │                │                │
        ▼                 ▼                ▼                ▼
    Sentiment         Retrieve RAG    Build Prompt    Call LLM
    Analysis          Context
        │                 │                │                │
        └─────────────────┼────────────────┴────────────────┘
                          │
                          ▼
                    Store Message
                    (BOT response)
                          │
                          ▼
                    Return Response
```

---

#### **GET /chat/history/{conversation_id}**
Retrieve conversation history.

**Input:**
- Path: `conversation_id` (string, required)
- Query: `limit` (int, optional, default: 50)
- Query: `offset` (int, optional, default: 0)

**Output:**
```json
{
  "conversation_id": "conv-001",
  "user_id": "user-123",
  "status": "OPEN",
  "messages": [
    {
      "id": "msg-001",
      "sender_type": "USER",
      "content": "What are your business hours?",
      "sentiment_score": 0.5,
      "created_at": "2026-02-14T15:20:00Z"
    },
    {
      "id": "msg-002",
      "sender_type": "BOT",
      "content": "Our business hours are...",
      "sentiment_score": 0.85,
      "created_at": "2026-02-14T15:30:00Z"
    }
  ],
  "total_messages": 2
}
```

---

### 3️⃣ Sentiment Analysis Endpoints

#### **POST /sentiment/analyze**
Analyze text sentiment.

**Input:**
```json
{
  "text": "I love your product! It works perfectly and customer service is amazing.",
  "context": "product_review"
}
```

**Processing Flow:**
```
1. Extract text and context
2. Apply Sentiment Strategies:
   - LexiconStrategy: Score based on sentiment lexicon
   - PatternStrategy: Pattern matching for emotions
   - StatisticalStrategy: ML-based scoring
3. Combine scores (weighted average)
4. Apply SentimentRulesEngine for overrides
5. Calculate confidence level
6. Store in SentimentLog
7. Return result
```

**Output:**
```json
{
  "text": "I love your product! It works perfectly...",
  "sentiment": {
    "score": 0.92,
    "label": "POSITIVE",
    "confidence": 0.95
  },
  "analysis": {
    "lexicon_score": 0.90,
    "pattern_score": 0.95,
    "statistical_score": 0.91
  },
  "analysis_id": "sentiment-12345",
  "created_at": "2026-02-14T15:35:00Z"
}
```

**Sentiment Labels:**
- `POSITIVE` (score: 0.5 - 1.0)
- `NEUTRAL` (score: 0.3 - 0.7)
- `NEGATIVE` (score: 0.0 - 0.5)

---

#### **GET /sentiment/logs**
Retrieve sentiment analysis logs.

**Input Query Parameters:**
- `start_date` (ISO datetime, optional)
- `end_date` (ISO datetime, optional)
- `sentiment` (POSITIVE|NEUTRAL|NEGATIVE, optional)
- `limit` (int, optional, default: 50)

**Output:**
```json
{
  "total": 150,
  "logs": [
    {
      "id": "sentiment-12345",
      "user_id": "user-123",
      "text": "I love your product!",
      "score": 0.92,
      "label": "POSITIVE",
      "created_at": "2026-02-14T15:35:00Z"
    }
  ]
}
```

---

### 4️⃣ Document Ingestion Endpoints

#### **POST /ingest/upload**
Upload and process document for RAG.

**Input:**
```
Content-Type: multipart/form-data

- file: (binary, .pdf/.txt/.docx)
- document_type: "pdf" | "text" | "docx"
- description: "Product manual section" (optional)
```

**Processing Flow:**
```
1. Upload file to temp storage
2. Extract text from document (PDF/DOCX parser)
3. Chunk document (overlap: 512 tokens, size: 1024 tokens)
4. Create Chunk records in PostgreSQL
5. Generate embeddings for each chunk:
   - Use embedding model (Sentence-transformers)
   - Create vectors (dimension: 384)
6. Ingest vectors into Qdrant:
   - Store with metadata (doc_id, chunk_index, etc.)
   - Create vector collection "rag_documents"
7. Create Document record with metadata
8. Return ingestion result
```

**Output:**
```json
{
  "document_id": "doc-67890",
  "filename": "product_manual.pdf",
  "document_type": "pdf",
  "total_chunks": 45,
  "chunks_indexed": 45,
  "status": "PROCESSED",
  "created_at": "2026-02-14T15:40:00Z",
  "message": "Document successfully ingested and indexed"
}
```

**Ingestion Workflow Diagram:**
```
Upload File
    │
    ▼
Extract Text
    │
    ▼
Split into Chunks
(overlap strategy)
    │
    ├─────────────────┬─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
Save Chunks    Generate         Store in
in PostgreSQL  Embeddings       Qdrant
    │                 │                 │
    └─────────────────┼─────────────────┘
                      │
                      ▼
            Create Document Record
                      │
                      ▼
            Return Success Response
```

---

### 5️⃣ Sentiment-Related Endpoints

#### **GET /sentiment/summary**
Get sentiment analytics summary.

**Input Query:**
```
GET /sentiment/summary?days=7
```

**Output:**
```json
{
  "period_days": 7,
  "total_analyzed": 245,
  "sentiment_distribution": {
    "positive": 165,
    "neutral": 50,
    "negative": 30
  },
  "average_score": 0.68,
  "trend": "UP"
}
```

---

### 6️⃣ Ticket Management Endpoints

#### **POST /tickets**
Create support ticket.

**Input:**
```json
{
  "conversation_id": "conv-001",
  "title": "Unable to login to account",
  "description": "Getting 'Invalid password' error after password reset",
  "priority": "HIGH",
  "category": "account_issue"
}
```

**Processing Flow:**
```
1. Validate input schema
2. Check conversation exists
3. Create Ticket record with:
   - status: OPEN
   - created_by_id: current_user.id
   - created_at: now()
4. Retrieve SLA policy based on department + priority
5. Calculate sla_due_at = now() + first_response_minutes
6. Evaluate escalation rules
7. Assign to appropriate agent (routing.py)
8. Send notification to assigned agent
9. Create audit log
10. Return ticket details
```

**Output:**
```json
{
  "id": "ticket-001",
  "conversation_id": "conv-001",
  "title": "Unable to login to account",
  "status": "OPEN",
  "priority": "HIGH",
  "assigned_agent_id": "agent-123",
  "created_by_id": "user-456",
  "created_at": "2026-02-14T15:45:00Z",
  "sla_due_at": "2026-02-14T17:45:00Z",
  "sla_breached": false
}
```

---

#### **GET /tickets**
List all tickets (with filters).

**Input Query:**
```
GET /tickets?status=OPEN&priority=HIGH&assigned_agent_id=agent-123&limit=20
```

**Output:**
```json
{
  "total": 45,
  "tickets": [
    {
      "id": "ticket-001",
      "title": "Unable to login...",
      "status": "OPEN",
      "priority": "HIGH",
      "assigned_agent_id": "agent-123",
      "sla_breached": false,
      "created_at": "2026-02-14T15:45:00Z"
    }
  ]
}
```

---

#### **PUT /tickets/{ticket_id}**
Update ticket.

**Input:**
```json
{
  "status": "IN_PROGRESS",
  "priority": "MEDIUM",
  "notes": "Investigating user account permissions"
}
```

**Output:**
```json
{
  "id": "ticket-001",
  "status": "IN_PROGRESS",
  "priority": "MEDIUM",
  "updated_at": "2026-02-14T16:00:00Z"
}
```

---

### 7️⃣ User Management Endpoints

#### **GET /users**
List all users.

**Input Query:**
```
GET /users?is_active=true&role=agent&limit=20
```

**Output:**
```json
{
  "total": 12,
  "users": [
    {
      "id": "user-123",
      "email": "agent@company.com",
      "full_name": "John Doe",
      "is_active": true,
      "roles": ["agent", "supervisor"],
      "created_at": "2025-06-15T10:00:00Z"
    }
  ]
}
```

---

#### **POST /users**
Create new user (Admin only).

**Input:**
```json
{
  "email": "newagent@company.com",
  "password": "securepass123",
  "full_name": "Jane Smith",
  "roles": ["agent"]
}
```

**Output:**
```json
{
  "id": "user-789",
  "email": "newagent@company.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "roles": ["agent"]
}
```

---

#### **PUT /users/{user_id}**
Update user.

**Input:**
```json
{
  "full_name": "John Smith Updated",
  "roles": ["agent", "supervisor"]
}
```

**Output:**
```json
{
  "id": "user-123",
  "full_name": "John Smith Updated",
  "roles": ["agent", "supervisor"],
  "updated_at": "2026-02-14T16:10:00Z"
}
```

---

### 8️⃣ Health Check Endpoints

#### **GET /health/**
Liveness probe.

**Output:**
```json
{
  "status": "alive",
  "timestamp": "2026-02-14T16:15:00Z"
}
```

---

#### **GET /health/ready**
Readiness probe (checks DB, Vector DB, LLM).

**Output:**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "vector_db": "ok",
    "llm": "ok"
  },
  "timestamp": "2026-02-14T16:15:00Z"
}
```

---

## 🔄 System Flow

### 1. User Message Processing Flow

```
User sends message
        │
        ▼
  ┌─────────────┐
  │ FastAPI     │ Validate HTTP request
  │ /chat/msg   │ Check JWT token
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Auth Layer  │ Verify permissions
  │ (RBAC)      │ Check user role
  └──────┬──────┘
         │
         ▼
  ┌──────────────────┐
  │ Sentiment Engine │ Analyze user sentiment
  │ (strategies.py)  │ Lexicon + Pattern + Stats
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ RAG Retriever    │ 1. Embed user message
  │ (retriever.py)   │ 2. Query Qdrant vectors
  │                  │ 3. Retrieve top-k chunks
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ Prompt Builder   │ Build LLM prompt with:
  │ (prompt_builder) │ - System instructions
  │                  │ - User message
  │                  │ - Retrieved context
  │                  │ - Conversation history
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ LLM Client       │ Call LLM API:
  │ (llm/client.py)  │ - OpenAI GPT
  │                  │ - Claude, etc.
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ Guardrails       │ Validate response:
  │ (guardrails.py)  │ - Toxicity check
  │                  │ - Fact verification
  │                  │ - Privacy compliance
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ Store Results    │ Save to DB:
  │ (engine.py)      │ - Message record
  │                  │ - Sentiment log
  │                  │ - Conversation update
  └──────┬───────────┘
         │
         ▼
  Return JSON response to client
```

### 2. Document Ingestion Flow

```
User uploads document
        │
        ▼
  ┌──────────────┐
  │ File Parser  │ Extract text:
  │ (chunker.py) │ - PDF → text
  │              │ - DOCX → text
  │              │ - TXT → raw
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Chunking     │ Split into chunks:
  │ (chunker.py) │ - Size: 1024 tokens
  │              │ - Overlap: 512 tokens
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────┐
  │ Embedding Generation │ For each chunk:
  │ (embedding.py)       │ 1. Convert to vector
  │                      │ 2. Dimension: 384
  │                      │ 3. Normalize
  └──────┬───────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌─────────┐ ┌─────────────┐
│PostgreSQL  │ Qdrant  │
│ Chunks  │ Vectors │
│ Metadata│ Search  │
└─────────┘ └─────────────┘
    │          │
    └────┬─────┘
         │
         ▼
  ┌──────────────┐
  │ Create Doc   │ Status: PROCESSED
  │ Record       │
  └──────┬───────┘
         │
         ▼
  Return ingestion status
```

### 3. Ticket Creation & Escalation Flow

```
Ticket created
        │
        ▼
  ┌──────────────┐
  │ Load SLA     │ Based on:
  │ Policy       │ - Department
  │              │ - Priority level
  └──────┬───────┘
         │
         ▼
  ┌──────────────────┐
  │ Calculate SLA    │ sla_due_at =
  │ Deadline         │ now() + first_response_min
  └──────┬───────────┘
         │
         ▼
  ┌──────────────┐
  │ Route Ticket │ Evaluate routing rules:
  │ (routing.py) │ - Keyword matching
  │              │ - Load balancing
  │              │ - Skill matching
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Assign Agent │ Select best agent
  │              │ assigned_agent_id
  └──────┬───────┘
         │
         ▼
  ┌──────────────────┐
  │ Send Alert       │ Notify assigned agent
  │ (notifications) │ (email/push)
  └──────┬───────────┘
         │
         ▼
  Background Scheduler monitors SLA:
  - Check sla_due_at
  - If breached: escalate_level++
  - Reassign to supervisor
  - Send escalation alert
```

---

## ⚙️ Environment Setup

### `.env` Configuration

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/sentiment_bot
DATABASE_ECHO=false

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_API_KEY=sk-...
LLM_API_URL=https://api.openai.com/v1

# Vector DB (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=
VECTOR_COLLECTION_NAME=rag_documents

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_LANGUAGE=en

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# RAG Configuration
RAG_CHUNK_SIZE=1024
RAG_CHUNK_OVERLAP=512
RAG_TOP_K=5
```

---

## 🗄️ Database Schema

### Key Tables

#### **users**
```sql
id (UUID PK)
email (VARCHAR UNIQUE)
hashed_password (VARCHAR)
full_name (VARCHAR)
is_active (BOOLEAN)
is_verified (BOOLEAN)
metadata (JSON)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

#### **conversations**
```sql
id (UUID PK)
user_id (UUID FK → users)
assigned_agent_id (UUID FK → users, nullable)
status (ENUM: OPEN, CLOSED, ESCALATED)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

#### **messages**
```sql
id (UUID PK)
conversation_id (UUID FK → conversations)
sender_type (ENUM: USER, AGENT, BOT, SYSTEM)
sender_id (UUID FK → users, nullable)
content (TEXT)
sentiment_score (FLOAT, nullable)
created_at (TIMESTAMP)
```

#### **tickets**
```sql
id (UUID PK)
conversation_id (UUID FK → conversations)
title (VARCHAR)
description (TEXT)
status (ENUM: OPEN, IN_PROGRESS, RESOLVED, CLOSED)
priority (ENUM: LOW, MEDIUM, HIGH, CRITICAL)
created_by_id (UUID FK → users)
assigned_agent_id (UUID FK → users, nullable)
department_id (UUID FK → departments, nullable)
sla_due_at (TIMESTAMP)
sla_breached (BOOLEAN)
escalation_level (INTEGER)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

#### **documents**
```sql
id (UUID PK)
owner_id (UUID FK → users)
name (VARCHAR)
document_type (VARCHAR)
file_path (VARCHAR, nullable)
file_size (INTEGER, nullable)
content_type (VARCHAR)
page_count (INTEGER, nullable)
chunk_count (INTEGER)
is_processed (BOOLEAN)
metadata (JSON)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

#### **chunks**
```sql
id (UUID PK)
document_id (UUID FK → documents)
chunk_index (INTEGER)
content (TEXT)
embedding_id (UUID, nullable)
created_at (TIMESTAMP)
```

#### **sentiment_logs**
```sql
id (UUID PK)
user_id (UUID FK → users)
text (TEXT)
score (FLOAT)
label (VARCHAR)
confidence (FLOAT)
metadata (JSON)
created_at (TIMESTAMP)
```

---

## ✨ Key Features

### 1. **Authentication & Authorization**
- JWT token-based authentication
- Role-Based Access Control (RBAC)
- User roles: admin, supervisor, agent, customer
- Permission-based endpoint access

### 2. **Sentiment Analysis**
- **Multi-Strategy Approach:**
  - Lexicon-based (VADER, AFINN)
  - Pattern matching (regex-based)
  - Statistical ML models
- Real-time sentiment scores
- Confidence levels
- Sentiment trend analysis

### 3. **RAG (Retrieval-Augmented Generation)**
- Document ingestion (PDF, DOCX, TXT)
- Automatic chunking with overlap
- Vector embeddings (Sentence-Transformers)
- Similarity search in Qdrant
- Context-aware responses

### 4. **Support Ticket Management**
- Ticket creation and tracking
- Automatic routing based on rules
- SLA monitoring and alerts
- Escalation workflows
- Agent assignment

### 5. **LLM Integration**
- Multi-provider support (OpenAI, Anthropic, etc.)
- Streaming responses
- Response guardrails
- Prompt engineering
- Token usage tracking

### 6. **Background Tasks**
- SLA breach monitoring
- Notification sending
- Document reindexing
- Scheduled reports

### 7. **Audit & Logging**
- Comprehensive audit trails
- Request/response logging
- Performance monitoring
- Security event logging

---

## 🔐 Security Features

✅ **HTTPS Ready** (SSL/TLS in production)  
✅ **CORS Protected** (configurable origins)  
✅ **SQL Injection Prevention** (SQLAlchemy ORM)  
✅ **XSS Protection** (Pydantic validation)  
✅ **Password Hashing** (bcrypt)  
✅ **JWT Token Expiration** (configurable)  
✅ **Rate Limiting** (per endpoint)  
✅ **Request Validation** (Pydantic schemas)

---

## 📊 Performance Optimization

- **Vectorized Operations**: Batch embedding processing
- **Caching**: Response caching for frequent queries
- **Indexing**: Database and vector DB indexing
- **Connection Pooling**: SQLAlchemy pool management
- **Async Processing**: Background task queue
- **Lazy Loading**: ORM relationship lazy loading

---

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure strong `JWT_SECRET_KEY`
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure PostgreSQL password
- [ ] Set up Qdrant authentication
- [ ] Configure LLM API keys
- [ ] Enable request rate limiting
- [ ] Set up monitoring & alerts
- [ ] Configure backup strategies
- [ ] Enable logging aggregation

---

## 📝 License

This project is part of Mahavir Group Software Development initiatives.

---

## 👥 Contributors

- **Development Team**: Mahavir Group
- **Repository**: [ai-chat-bot](https://github.com/Naveencodespeaks/ai-chat-bot)

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact development team
- Review documentation in `/docs` folder

---

## 🔗 Quick Links

- [Architecture Documentation](docs/architecture.md)
- [Security Policies](docs/security.md)
- [Deployment Guide](docs/deployment.md)
- [RBAC Matrix](docs/rbac_matrix.md)
- [API Docs (Live)](http://127.0.0.1:8000/docs)

---

**Last Updated:** February 14, 2026  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
