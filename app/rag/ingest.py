from uuid import uuid4
from qdrant_client.models import PointStruct

def ingest_document(
    client,
    text: str,
    embedding: list[float],
    metadata: dict
):
    point = PointStruct(
        id=str(uuid4()),
        vector=embedding,
        payload={
            "text": text,
            **metadata
        }
    )

    client.upsert(
        collection_name="rag_documents",
        points=[point]
    )


def ingest_chunk(
    *,
    client,
    embedding,
    text: str,
    document_id: str,
    allowed_roles: list[str],
    department: str,
    visibility: str,
):
    client.upsert(
        collection_name="rag_documents",
        points=[
            {
                "id": f"{document_id}-{hash(text)}",
                "vector": embedding,
                "payload": {
                    "document_id": document_id,
                    "allowed_roles": allowed_roles,
                    "department": department,
                    "visibility": visibility,
                    "text": text,
                },
            }
        ],
    )
