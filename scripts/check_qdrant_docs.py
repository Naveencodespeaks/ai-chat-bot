from app.db.vector import get_qdrant_client
from app.core.config import settings

client = get_qdrant_client()

print("\nCollections:")
print(client.get_collections())

print("\nFirst 5 points in collection:")
points = client.scroll(
    collection_name=settings.RAG_COLLECTION,
    limit=5,
    with_payload=True,
)

for p in points[0]:
    print(p.payload)
