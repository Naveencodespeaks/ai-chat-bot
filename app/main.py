from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ✅ Use ONLY your project logger
from app.core.logging import logger

# Routers
from app.api.secure_test import router as secure_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router
from app.api.ingest import router as ingest_router
from app.api.sentiment import router as sentiment_router
from app.api.users import router as users_router
from app.api.tickets import router as tickets_router
from app.api.health import router as health_router

# Vector DB setup
# from app.db.vector import vector_client
from app.rag.vector_schema import ensure_collection
from app.core.config import settings
from app.core.scheduler import start_scheduler
from app.db.vector import get_qdrant_client



app = FastAPI(
    title="AI RAG Sentiment Bot",
    description=(
        "An AI-powered RAG (Retrieval-Augmented Generation) "
        "Sentiment Bot that analyzes and generates responses "
        "based on user input and enterprise support workflows."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include all API routes
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(sentiment_router)
app.include_router(users_router)
app.include_router(tickets_router)
app.include_router(secure_router)


@app.get("/")
def read_root():
    return {"status": "AI RAG Sentiment Bot is running"}


# ✅ SINGLE startup handler
@app.on_event("startup")
def startup_event():
    logger.info("AI RAG Sentiment Bot is starting up...")

    # Ensure vector collection exists
    ensure_collection(
        get_qdrant_client(),
        settings.RAG_COLLECTION,
    )

    logger.info(
        f"Vector collection ensured: {settings.RAG_COLLECTION}"
    )


@app.on_event("shutdown")
def shutdown_event():
    logger.info("AI RAG Sentiment Bot is shutting down...")



@app.on_event("startup")
def start_jobs():
    start_scheduler()
