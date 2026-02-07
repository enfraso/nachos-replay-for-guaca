"""Nachos Replay for Guaca - API Package"""
from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.replays import router as replays_router
from app.api.audit import router as audit_router
from app.api.stats import router as stats_router
from app.api.users import router as users_router, groups_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(replays_router)
api_router.include_router(audit_router)
api_router.include_router(stats_router)
api_router.include_router(users_router)
api_router.include_router(groups_router)

__all__ = ["api_router"]
