# app/rag/ingest.py

from __future__ import annotations

from dataclasses import dataclass
from app.db.vector import ensure_collection
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
import hashlib
import re
import uuid

from app.auth.context import UserContext
from app.core.config import settings
from app.core.logging import get_logger

# Embeddings (prefer embed_text/embed_chunks if you have them; fallback to embed_query)
try:
    from app.rag.embedding import embed_text  # type: ignore
except Exception:
    embed_text = None  # fallback later

from app.rag.embedding import embed_query  # you already have this

logger = get_logger(__name__)


# -----------------------------
# CONFIG DEFAULTS (safe fallbacks)
# -----------------------------
DEFAULT_CHUNK_SIZE = getattr(settings, "RAG_CHUNK_SIZE", 900)
DEFAULT_CHUNK_OVERLAP = getattr(settings, "RAG_CHUNK_OVERLAP", 150)
DEFAULT_TOP_K = getattr(settings, "RAG_TOP_K", 5)
DEFAULT_COLLECTION = getattr(settings, "RAG_COLLECTION", "mahavir_docs")
DEFAULT_VISIBILITY = getattr(settings, "RAG_DEFAULT_VISIBILITY", ["INTERNAL"])
DEFAULT_ALLOWED_ROLES = getattr(settings, "RAG_DEFAULT_ALLOWED_ROLES", ["ADMIN"])
DEFAULT_DEPARTMENT = getattr(settings, "RAG_DEFAULT_DEPARTMENT", "General")

# Optional: enable SQL persistence if you want (default off)
PERSIST_TO_SQL = bool(getattr(settings, "RAG_PERSIST_TO_SQL", False))

# Optional: Qdrant vector size / distance. If not configured, auto-detect from first embedding.
CONFIG_VECTOR_SIZE = getattr(settings, "RAG_VECTOR_SIZE", None)
CONFIG_DISTANCE = getattr(settings, "RAG_DISTANCE", "Cosine")  # "Cosine" is typical


# -----------------------------
# DATA STRUCTURES
# -----------------------------
@dataclass
class IngestMeta:
    doc_id: str
    title: str
    source: str
    department: str
    allowed_roles: List[str]
    visibility: List[str]
    tags: List[str]
    created_by: str


@dataclass
class IngestResult:
    doc_id: str
    collection: str
    chunks_ingested: int
    points_upserted: int
    department: str
    allowed_roles: List[str]
    visibility: List[str]
    source: str
    title: str
    tags: List[str]
    status: str


# -----------------------------
# NORMALIZATION / VALIDATION
# -----------------------------
def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(text: str) -> str:
    """
    Normalizes text for better chunking & retrieval.
    Keeps content intact but removes noisy spacing.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # trim spaces per line
    text = "\n".join(line.strip() for line in text.split("\n"))
    # collapse repeated spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

from app.auth.context import UserContext


from app.auth.context import UserContext
from app.core.logging import get_logger

logger = get_logger(__name__)


def _assert_verified_ingest(user_context: UserContext) -> None:
    """
    Security gate for RAG ingestion.

    Logs all ingestion attempts for audit trail.
    Only verified ADMIN users are allowed to ingest documents.
    """

    # -----------------------------
    # Log ingestion attempt
    # -----------------------------
    logger.warning(
        f"[INGEST ATTEMPT] "
        f"user={getattr(user_context, 'user_id', 'unknown')} "
        f"roles={getattr(user_context, 'roles', [])} "
        f"dept={getattr(user_context, 'department', None)}"
    )

    # -----------------------------
    # Basic Validation
    # -----------------------------
    if not user_context:
        logger.error("[INGEST BLOCKED] Missing user context")
        raise PermissionError("Missing user context")

    if not getattr(user_context, "is_verified", False):
        logger.error(
            f"[INGEST BLOCKED] Unverified user "
            f"user={getattr(user_context, 'user_id', 'unknown')}"
        )
        raise PermissionError("User is not verified")

    # -----------------------------
    # Role Check (case-safe)
    # -----------------------------
    roles = [r.upper() for r in (user_context.roles or [])]

    if "ADMIN" not in roles and "SUPERADMIN" not in roles:
        logger.error(
            f"[INGEST BLOCKED] Not admin "
            f"user={getattr(user_context, 'user_id', 'unknown')} "
            f"roles={roles}"
        )
        raise PermissionError("Only ADMIN users can ingest documents")

    # -----------------------------
    # Department Check
    # -----------------------------
    if not getattr(user_context, "department", None):
        logger.error(
            f"[INGEST BLOCKED] Missing department "
            f"user={getattr(user_context, 'user_id', 'unknown')}"
        )
        raise PermissionError("Department must be set for ingestion")

    # -----------------------------
    # Passed all checks
    # -----------------------------
    logger.info(
        f"[INGEST ALLOWED] "
        f"user={getattr(user_context, 'user_id', 'unknown')} "
        f"roles={roles} "
        f"dept={getattr(user_context, 'department', None)}"
    )




def _validate_meta(
    *,
    title: str,
    source: str,
    department: Optional[str],
    allowed_roles: Optional[List[str]],
    visibility: Optional[List[str]],
    tags: Optional[List[str]],
) -> Tuple[str, str, str, List[str], List[str], List[str]]:
    title = (title or "").strip()
    source = (source or "").strip()

    if not title:
        raise ValueError("title is required")
    if not source:
        raise ValueError("source is required")

    # dept = (department or DEFAULT_DEPARTMENT).strip()
    dept = (department or DEFAULT_DEPARTMENT).strip().upper()

    roles = allowed_roles or list(DEFAULT_ALLOWED_ROLES)
    vis = visibility or list(DEFAULT_VISIBILITY)
    tg = tags or []

    # hard validation
    if not isinstance(roles, list) or not all(isinstance(x, str) and x.strip() for x in roles):
        raise ValueError("allowed_roles must be a non-empty list of strings")
    if not isinstance(vis, list) or not all(isinstance(x, str) and x.strip() for x in vis):
        raise ValueError("visibility must be a non-empty list of strings")
    if not isinstance(tg, list) or not all(isinstance(x, str) for x in tg):
        raise ValueError("tags must be a list of strings")

    # normalize values
    roles = [r.strip().upper() for r in roles]
    vis = [v.strip().upper() for v in vis]
    tg = [t.strip() for t in tg if t.strip()]

    return title, source, dept, roles, vis, tg


def _stable_doc_id(*, title: str, source: str, department: str) -> str:
    """
    Stable-ish doc_id for re-ingest updates.
    If you want always-new doc ids, replace with uuid4().
    """
    raw = f"{title}|{source}|{department}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


# -----------------------------
# CHUNKING
# -----------------------------
def _fallback_chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Simple, reliable chunker:
    - prefers paragraph boundaries
    - uses overlap for context continuity
    """
    if chunk_size <= 200:
        chunk_size = 200
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = max(50, chunk_size // 6)

    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for p in paras:
        if not current:
            current = p
            continue
        if len(current) + 2 + len(p) <= chunk_size:
            current = current + "\n\n" + p
        else:
            flush()
            current = p

    flush()

    # add overlap by sliding window on chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = []
        for i, c in enumerate(chunks):
            if i == 0:
                overlapped.append(c)
                continue
            prev = overlapped[-1]
            tail = prev[-overlap:] if len(prev) > overlap else prev
            overlapped.append((tail + "\n\n" + c).strip())
        chunks = overlapped

    return chunks


def chunk_document(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Uses your rag/chunker.py if available, otherwise fallback.
    """
    try:
        from app.rag.chunker import chunk_text  # type: ignore
        return chunk_text(text, chunk_size=chunk_size, overlap=overlap)  # if your signature supports it
    except Exception:
        return _fallback_chunk_text(text, chunk_size, overlap)


# -----------------------------
# EMBEDDINGS
# -----------------------------
def embed_chunk(text: str) -> List[float]:
    """
    Uses embed_text if present else uses embed_query (works for chunks too).
    """
    if embed_text is not None:
        return embed_text(text)  # type: ignore
    return embed_query(text)


# -----------------------------
# QDRANT HELPERS (ensure collection + upsert)
# -----------------------------
def ensure_collection_exists(client: Any, collection: str, vector_size: int, distance: str) -> None:
    """
    Creates Qdrant collection if missing.
    Works with QdrantClient (qdrant-client).
    """
    try:
        existing = client.get_collections()
        names = {c.name for c in existing.collections}
        if collection in names:
            return
    except Exception:
        # Some QdrantClient versions: use has_collection
        try:
            if client.collection_exists(collection_name=collection):
                return
        except Exception:
            pass

    # Create collection
    logger.info(f"[RAG] Creating Qdrant collection={collection} vector_size={vector_size} distance={distance}")
    try:
        from qdrant_client.http import models as qmodels  # type: ignore

        dist = getattr(qmodels.Distance, distance, qmodels.Distance.COSINE)
        client.create_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=dist),
        )
    except Exception as e:
        # If create fails because it exists due to race, ignore
        logger.warning(f"[RAG] create_collection warning: {e}")


def upsert_points(client: Any, collection: str, points: List[Dict[str, Any]]) -> int:
    """
    Upserts points to Qdrant. Returns points count.
    """
    if not points:
        return 0

    # qdrant-client accepts dict points or PointStruct models depending on version
    try:
        from qdrant_client.http import models as qmodels  # type: ignore
        qpoints = [
            qmodels.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points
        ]
        client.upsert(collection_name=collection, points=qpoints)
        return len(qpoints)
    except Exception:
        client.upsert(collection_name=collection, points=points)
        return len(points)


# -----------------------------
# OPTIONAL SQL PERSISTENCE (kept safe/off by default)
# -----------------------------
def _maybe_persist_to_sql(db: Any, meta: IngestMeta, chunks: List[str]) -> None:
    """
    Optional persistence into Postgres tables (documents, chunks).
    This is OFF by default via settings.RAG_PERSIST_TO_SQL.
    Implement exact ORM save based on your models if you want.
    """
    if not PERSIST_TO_SQL:
        return
    if db is None:
        logger.warning("[RAG][SQL] db session not provided; skipping SQL persistence")
        return

    try:
        from app.models.documents import Document  # type: ignore
        from app.models.chunk import Chunk  # type: ignore
    except Exception as e:
        logger.warning(f"[RAG][SQL] Models missing or import failed: {e}")
        return

    # Minimal safe insert/update pattern
    try:
        # Upsert document
        doc = db.get(Document, meta.doc_id)
        if not doc:
            doc = Document(
                id=meta.doc_id,
                title=meta.title,
                source=meta.source,
                department=meta.department,
                allowed_roles=meta.allowed_roles,
                visibility=meta.visibility,
                tags=meta.tags,
                created_by=meta.created_by,
            )
            db.add(doc)

        # Replace chunks (simple strategy)
        # If you already have relationships, adjust this logic.
        # Delete old chunks for doc_id if needed:
        try:
            db.query(Chunk).filter(Chunk.document_id == meta.doc_id).delete()  # type: ignore
        except Exception:
            pass

        for idx, c in enumerate(chunks):
            db.add(
                Chunk(
                    id=str(uuid.uuid4()),
                    document_id=meta.doc_id,
                    chunk_index=idx,
                    text=c,
                )
            )

        db.commit()
        logger.info(f"[RAG][SQL] persisted doc_id={meta.doc_id} chunks={len(chunks)}")
    except Exception as e:
        db.rollback()
        logger.error(f"[RAG][SQL] persist failed doc_id={meta.doc_id}: {e}")


# -----------------------------
# MAIN INGEST FUNCTION (PRODUCTION)
# -----------------------------
def ingest_document(
    *,
    client: Any,
    user_context: UserContext,
    ticket_id: Optional[str] = None,
    text: str,
    title: str,
    source: str,
    department: Optional[str] = None,
    allowed_roles: Optional[List[str]] = None,
    visibility: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    doc_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    db: Any = None,  # optional SQLAlchemy session
) -> IngestResult:
    """
    Production ingest:
    - validates user context
    - normalizes text
    - chunks
    - embeds
    - ensures Qdrant collection exists
    - upserts points with RBAC payload
    - optional SQL persistence
    """

    _assert_verified_ingest(user_context)

    if not text or not text.strip():
        raise ValueError("text is required")

    title, source, dept, roles, vis, tg = _validate_meta(
        title=title,
        source=source,
        department=department,
        allowed_roles=allowed_roles,
        visibility=visibility,
        tags=tags,
    )

    clean_text = _normalize_text(text)
    if len(clean_text) < 30:
        raise ValueError("text is too short to ingest")


    # collection = DEFAULT_COLLECTION
    collection = getattr(settings, "RAG_COLLECTION", DEFAULT_COLLECTION)

    chunk_size = int(chunk_size or DEFAULT_CHUNK_SIZE)
    overlap = int(overlap or DEFAULT_CHUNK_OVERLAP)

    # Determine doc_id: stable default (or pass explicit)
    doc_id_final = doc_id or _stable_doc_id(title=title, source=source, department=dept)

    meta = IngestMeta(
        doc_id=doc_id_final,
        title=title,
        source=source,
        department=dept,
        allowed_roles=roles,
        visibility=vis,
        tags=tg,
        created_by=str(getattr(user_context, "user_id", "unknown")),
    )

    logger.info(
        f"[RAG INGEST] start doc_id={meta.doc_id} title={meta.title!r} "
        f"dept={meta.department} roles={meta.allowed_roles} vis={meta.visibility} source={meta.source}"
    )

    # 1) Chunking
    chunks = chunk_document(clean_text, chunk_size=chunk_size, overlap=overlap)
    chunks = [c for c in chunks if c.strip()]
    if not chunks:
        raise ValueError("chunking produced zero chunks")

    logger.info(f"[RAG INGEST] chunked doc_id={meta.doc_id} chunks={len(chunks)}")

    # 2) Embeddings + points
    points: List[Dict[str, Any]] = []
    vector_size: Optional[int] = CONFIG_VECTOR_SIZE

    for idx, chunk in enumerate(chunks):
        vec = embed_chunk(chunk)
        if vector_size is None:
            vector_size = len(vec)

        # chunk_hash = hashlib.sha1(chunk.encode()).hexdigest()[:8]
        # chunk_id = f"{meta.doc_id}:{idx}:{chunk_hash}"
        chunk_id = str(uuid.uuid4())

        payload = {
            # ======================
            # IDs
            # ======================
            "document_id": meta.doc_id,
            "chunk_id": chunk_id,
            "chunk_index": idx,
            "ticket_id": ticket_id,

            # ======================
            # CONTENT
            # ======================
            "content": chunk,
            "text": chunk,  # keep for compatibility

            # ======================
            # RBAC SECURITY
            # ======================
            "allowed_roles": meta.allowed_roles,
            "visibility": meta.visibility,
            "department": meta.department,

            # ======================
            # METADATA
            # ======================
            "title": meta.title,
            "source": meta.source,
            "tags": meta.tags,
            "created_by": meta.created_by,
            "ingested_at": _utc_now_iso(),
        }

        points.append(
            {
                "id": chunk_id,
                "vector": vec,
                "payload": payload,
            }
        )


    if vector_size is None:
        raise RuntimeError("Unable to determine vector size (embedding failed?)")

    # 3) Ensure collection exists
    ensure_collection_exists(client, collection=collection, vector_size=vector_size, distance=CONFIG_DISTANCE)

    # 4) Upsert to Qdrant
    upserted = upsert_points(client, collection=collection, points=points)

    logger.info(f"[RAG INGEST] upserted doc_id={meta.doc_id} points={upserted} collection={collection}")

    # 5) Optional SQL persistence
    _maybe_persist_to_sql(db, meta, chunks)

    return IngestResult(
        doc_id=meta.doc_id,
        collection=collection,
        chunks_ingested=len(chunks),
        points_upserted=upserted,
        department=meta.department,
        allowed_roles=meta.allowed_roles,
        visibility=meta.visibility,
        source=meta.source,
        title=meta.title,
        tags=meta.tags,
        status="SUCCESS",
    )
