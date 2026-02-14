"""Backfill Qdrant vector DB with documents, chunks, and RBAC metadata.

Usage:
    python scripts/backfill_metadata.py \\
        --doc-path path/to/file.txt \\
        --department HR \\
        --roles ADMIN,USER \\
        --visibility INTERNAL
"""

import argparse
import logging
import sys
from pathlib import Path
from uuid import uuid4

from qdrant_client import QdrantClient

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.rag.chunker import chunk_by_size
from app.rag.embedding import embed_query


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_metadata(
    document_id: str,
    department: str,
    roles: list[str],
    visibility: str,
) -> dict:
    """Build a metadata payload for a chunk."""
    return {
        "document_id": document_id,
        "department": department,
        "allowed_roles": roles,
        "visibility": visibility,
    }


def ingest_document(
    client: QdrantClient,
    doc_path: str,
    department: str,
    roles: list[str],
    visibility: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> int:
    """Read a document, chunk it, embed, and ingest to Qdrant.

    Args:
        client: Qdrant client instance
        doc_path: Path to document file
        department: Department for RBAC
        roles: List of allowed roles
        visibility: Visibility level (PUBLIC, INTERNAL, CONFIDENTIAL)
        chunk_size: Character size per chunk
        chunk_overlap: Overlap between chunks

    Returns:
        Number of chunks ingested
    """
    # Read document
    doc_id = str(uuid4())
    doc_text = Path(doc_path).read_text(encoding="utf-8")
    logger.info(f"Read document: {doc_path} ({len(doc_text)} chars)")

    # Chunk
    chunks = chunk_by_size(doc_text, chunk_size=chunk_size, overlap=chunk_overlap)
    logger.info(f"Generated {len(chunks)} chunks")

    if not chunks:
        logger.warning("No chunks generated")
        return 0

    # Build metadata
    metadata = build_metadata(
        document_id=doc_id,
        department=department,
        roles=roles,
        visibility=visibility,
    )

    # Embed and ingest each chunk
    points = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = embed_query(chunk)
            point_id = f"{doc_id}-{i}"

            points.append(
                {
                    "id": hash(point_id) % (10**18),  # Qdrant wants numeric IDs
                    "vector": embedding,
                    "payload": {
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **metadata,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Failed to embed chunk {i}: {e}")
            continue

    if points:
        client.upsert(
            collection_name=settings.RAG_COLLECTION,
            points=points,
        )
        logger.info(f"Ingested {len(points)} points into {settings.RAG_COLLECTION}")

    return len(points)


def main():
    parser = argparse.ArgumentParser(description="Backfill Qdrant with document chunks")
    parser.add_argument("--doc-path", required=True, help="Path to document file")
    parser.add_argument(
        "--department", default="GENERAL", help="Department for RBAC (default: GENERAL)"
    )
    parser.add_argument(
        "--roles",
        default="USER",
        help="Comma-separated roles (default: USER)",
    )
    parser.add_argument(
        "--visibility",
        default="PUBLIC",
        choices=["PUBLIC", "INTERNAL", "CONFIDENTIAL"],
        help="Visibility level (default: PUBLIC)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Chunk size in characters (default: 512)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Overlap between chunks (default: 50)",
    )

    args = parser.parse_args()

    # Parse roles
    roles = [r.strip().upper() for r in args.roles.split(",")]

    # Validate inputs
    if not Path(args.doc_path).exists():
        logger.error(f"Document not found: {args.doc_path}")
        sys.exit(1)

    # Connect to Qdrant
    try:
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        logger.info(f"Connected to Qdrant at {settings.QDRANT_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        sys.exit(1)

    # Ingest
    try:
        count = ingest_document(
            client=client,
            doc_path=args.doc_path,
            department=args.department,
            roles=roles,
            visibility=args.visibility,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        logger.info(f"✓ Backfill complete: {count} chunks ingested")
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
 
