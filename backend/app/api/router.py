from fastapi import APIRouter

from app.api import auth, documents, examinations, questions, reports, knowledge

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(examinations.router, prefix="/examinations", tags=["examinations"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
