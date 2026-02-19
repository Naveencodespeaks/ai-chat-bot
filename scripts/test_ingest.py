from app.db.vector import get_qdrant_client
from app.rag.ingest import ingest_document
from app.auth.context import UserContext

client = get_qdrant_client()

admin = UserContext(
    user_id="admin1",
    role="ADMIN",
    department="HR"
)

text = """
Mahavir Group Leave Policy

Employees are entitled to:
- 12 casual leaves
- 12 sick leaves
- 20 earned leaves
"""

res = ingest_document(
    client=client,
    user_context=admin,
    text=text,
    title="Leave Policy",
    source="HR Manual",
    department="HR",
    allowed_roles=["HR_USER"],
    visibility=["INTERNAL"]
)

print(res)
