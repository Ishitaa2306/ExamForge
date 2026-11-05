"""
Settings and System Status API Endpoints.
Surfaces configuration status and live provider connectivity tests without exposing private keys.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.llm.model_router import get_gemini_client, get_granite_client

router = APIRouter()


@router.get("/status")
def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns application configuration and provider statuses without credentials."""
    # Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    gemini_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    granite_configured = bool(
        settings.WATSONX_API_KEY
        and settings.WATSONX_API_KEY.strip()
        and settings.WATSONX_PROJECT_ID
        and settings.WATSONX_PROJECT_ID.strip()
    )

    return {
        "application": {
            "name": "ExamForge",
            "version": "1.0.0",
            "ai_provider_mode": settings.AI_PROVIDER_MODE,
        },
        "database": {
            "connected": db_ok,
            "engine": settings.DATABASE_URL.split("://")[0] if "://" in settings.DATABASE_URL else "unknown",
        },
        "gemini": {
            "configured": gemini_configured,
            "model_id": settings.GEMINI_MODEL_ID,
            "provider": "Google Gemini",
        },
        "granite": {
            "configured": granite_configured,
            "model_id": settings.GRANITE_MODEL_ID,
            "watsonx_url": settings.WATSONX_URL,
            "provider": "IBM watsonx.ai Granite",
        },
    }


@router.post("/test-providers")
def test_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Executes actual test requests to Gemini and Granite to verify credentials and model accessibility.
    """
    gemini_result = {"status": "unconfigured"}
    granite_result = {"status": "unconfigured"}

    if settings.GEMINI_API_KEY:
        try:
            client = get_gemini_client()
            gemini_result = client.test_connection()
        except Exception as exc:
            gemini_result = {
                "status": "error",
                "message": str(exc),
                "model_id": settings.GEMINI_MODEL_ID,
            }

    if settings.WATSONX_API_KEY and settings.WATSONX_PROJECT_ID:
        try:
            client = get_granite_client()
            granite_result = client.test_connection()
        except Exception as exc:
            granite_result = {
                "status": "error",
                "message": str(exc),
                "model_id": settings.GRANITE_MODEL_ID,
            }

    return {
        "gemini": gemini_result,
        "granite": granite_result,
    }

