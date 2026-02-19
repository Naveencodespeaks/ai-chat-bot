from app.db.vector import get_qdrant_client
from app.rag.retriever import retrieve_context
from app.auth.context import UserContext


def main():
    client = get_qdrant_client()

    user_context = UserContext(
        user_id="test-user",
        role="HR_USER",
        department="HR",
    )

    results = retrieve_context(
        client=client,
        query="What is leave policy?",
        user_context=user_context,
        top_k=5,
    )

    print("\n=== RETRIEVED ===")
    for r in results:
        print(r.get("source"), r.get("department"))
        print(r.get("text")[:200])
        print("-" * 50)


if __name__ == "__main__":
    main()
