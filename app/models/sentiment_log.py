from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimestampMixin
from app.db.session import Base

class SentimentLog(Base, TimestampMixin):
    __tablename__ = "sentiment_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sentiment: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float)
