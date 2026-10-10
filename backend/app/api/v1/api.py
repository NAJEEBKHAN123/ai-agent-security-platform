from fastapi import APIRouter
from app.api.v1 import health, auth, chat, policies, approvals, events, dashboard

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(policies.router)
api_router.include_router(approvals.router)
api_router.include_router(events.router)
api_router.include_router(dashboard.router)


