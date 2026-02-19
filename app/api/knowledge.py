from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.knowledge_bot import CompanyKnowledgeBot
from app.auth.dependencies import get_current_user
from app.auth.context import UserContext

router = APIRouter()
bot = CompanyKnowledgeBot()


@router.post("/ask")
def ask_company_bot(
    message: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
):
    return bot.ask(db=db, user=user, message=message)
