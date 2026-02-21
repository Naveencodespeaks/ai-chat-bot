from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.enums import SenderType

from app.actions.escalation import escalate_ticket
from app.sentiment.analyzer import analyze_sentiment
from app.rag.retriever import retrieve_context
from app.llm.client import generate_response


# -------------------------------------------------
# ENTERPRISE CHAT ENGINE
# -------------------------------------------------
def process_user_message(
    db: Session,
    conversation: Conversation,
    user_id: int,
    content: str
) -> dict:
    """
    Enterprise AI Processing Flow

    1. Save user message
    2. Run sentiment analysis
    3. Retrieve RAG context
    4. Generate LLM response
    5. Save bot response
    6. Escalate in background if needed
    """

    # -------------------------------------------------
    # 1️⃣ Sentiment Analysis
    # -------------------------------------------------
    sentiment_score = analyze_sentiment(content)

    # -------------------------------------------------
    # 2️⃣ Save USER Message
    # -------------------------------------------------
    user_message = Message(
        conversation_id=conversation.id,
        sender_type=SenderType.USER,
        sender_id=user_id,
        content=content,
        sentiment_score=sentiment_score
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # -------------------------------------------------
    # 3️⃣ RAG Retrieval
    # -------------------------------------------------
    context_chunks = retrieve_context(content)

    # -------------------------------------------------
    # 4️⃣ LLM Response Generation
    # -------------------------------------------------
    bot_reply = generate_response(
        user_message=content,
        context=context_chunks
    )

    # -------------------------------------------------
    # 5️⃣ Save BOT Message
    # -------------------------------------------------
    bot_message = Message(
        conversation_id=conversation.id,
        sender_type=SenderType.BOT,
        sender_id=None,
        content=bot_reply,
        sentiment_score=None
    )

    db.add(bot_message)
    db.commit()

    # -------------------------------------------------
    # 6️⃣ Escalation Check (Background Logic)
    # -------------------------------------------------
    ticket = escalate_ticket(
        db=db,
        conversation_id=conversation.id,
        message_id=user_message.id,
        sentiment_score=sentiment_score
    )

    # -------------------------------------------------
    # 7️⃣ Final Response Object
    # -------------------------------------------------
    result = {
        "reply": bot_reply,
        "sentiment_score": sentiment_score,
        "escalated": False,
        "ticket_id": None
    }

    if ticket:
        result["escalated"] = True
        result["ticket_id"] = ticket.id

    return result
