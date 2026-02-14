from qdrant_client.models import VectorParams, Distance
from qdrant_client.http import models as qmodels

VECTOR_DIMENSION = 768

def create_collection(client):
    client.recreate_collection(
        collection_name="rag_documents",
        vectors_config=VectorParams(
            size=1536,  # OpenAI embedding size
            distance=Distance.COSINE
        )
    )


def ensure_collection(client, collection_name: str):
    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=qmodels.VectorParams(
            size=VECTOR_DIMENSION,
            distance=qmodels.Distance.COSINE,
        ),
    )