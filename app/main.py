from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Vector DB
from app.db.vector import get_qdrant_client, ensure_collection
from app.core.config import settings
from app.core.scheduler import start_scheduler

app = FastAPI(
    title="AI RAG Sentiment Bot",
    description="Enterprise AI HelpDesk with RAG + Sentiment",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# ROUTERS
# -----------------------------
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


# -----------------------------
# STARTUP
# -----------------------------
@app.on_event("startup")
def startup_event():
    logger.info("AI RAG Sentiment Bot is starting up...")

    try:
        client = get_qdrant_client()

        # ⚠️ Use embedding size or config
        vector_size = getattr(settings, "RAG_VECTOR_SIZE", 1536)

        ensure_collection(
            collection_name=settings.RAG_COLLECTION,
            vector_size=vector_size,
        )

        logger.info(f"Vector collection ensured: {settings.RAG_COLLECTION}")

    except Exception as e:
        logger.error(f"Vector DB init failed: {e}")
        raise

    # Start background scheduler
    try:
        start_scheduler()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")


# -----------------------------
# SHUTDOWN
# -----------------------------
@app.on_event("shutdown")
def shutdown_event():
    logger.info("AI RAG Sentiment Bot is shutting down...")
