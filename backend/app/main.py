from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.api.v1.api import api_router
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def init_db():
    """Create all database tables and seed initial demo accounts."""
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed standard accounts if table is empty
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            demo_users = [
                ("analyst@agentsec.com", "Security Analyst", "AnalystPass123!", UserRole.REVIEWER),
                ("admin@agentsec.com", "Security Administrator", "AdminPass123!", UserRole.ADMIN),
                ("user@agentsec.com", "Standard User", "UserPass123!", UserRole.USER),
            ]
            for email, name, pwd, role in demo_users:
                db.add(User(
                    email=email,
                    full_name=name,
                    password_hash=get_password_hash(pwd),
                    role=role,
                    is_active=True,
                ))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database schema & seed accounts
    init_db()
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Security Guardrail Platform for AI Agents: Prompt Injection Detection, Action Monitoring, and Human Approval.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root health convenience endpoint
@app.get("/health", tags=["Health"])
def root_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "api_v1": settings.API_V1_STR,
    }
