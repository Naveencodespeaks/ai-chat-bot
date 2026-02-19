# from dotenv import load_dotenv
# import os

# load_dotenv()

# class Settings:
#     APP_NAME: str = os.getenv("APP_NAME", "AI RAG Sentiment Bot")
#     APP_ENV: str = os.getenv("APP_ENV", "dev")
#     LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
#     PORT: int = int(os.getenv("PORT", 8000))

#     DATABASE_URL: str = os.getenv("DATABASE_URL")
#     if not DATABASE_URL:
#         raise ValueError("DATABASE_URL is not set in .env")

#     RAG_COLLECTION: str = os.getenv("RAG_COLLECTION", "rag_documents")
#     RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", 5))

#     QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
#     QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY")

# settings = Settings()



from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AI RAG Sentiment Bot")
    APP_ENV: str = os.getenv("APP_ENV", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", 8000))

    DATABASE_URL: str = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in .env")

    RAG_COLLECTION: str = os.getenv("RAG_COLLECTION", "rag_documents")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", 5))

    # -----------------------------
    # QDRANT CONFIG
    # -----------------------------
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY")
    QDRANT_TIMEOUT: int = int(os.getenv("QDRANT_TIMEOUT", 60))   # ✅ ADD THIS
    RAG_VECTOR_SIZE: int = int(os.getenv("RAG_VECTOR_SIZE", 1536))

settings = Settings()
