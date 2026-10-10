from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Register a new user with email and secure password."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )
    
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role or UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login_json(credentials: UserLogin, db: Session = Depends(get_db)) -> Any:
    """Authenticate user with JSON credentials and return JWT bearer token."""
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=access_token_expires,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "user_id": user.id,
        "email": user.email,
    }


@router.post("/token", response_model=Token, include_in_schema=False)
def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """OAuth2 compatible token login for Swagger UI documentation authorizer."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "user_id": user.id,
        "email": user.email,
    }


@router.get("/me", response_model=UserResponse)
def read_current_user_profile(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieve profile and role information of currently authenticated user."""
    return current_user


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_initial_demo_accounts(db: Session = Depends(get_db)) -> Any:
    """Seed initial demonstration accounts for presentation/evaluation if they do not exist."""
    demo_accounts = [
        ("analyst@agentsec.com", "Security Analyst", "AnalystPass123!", UserRole.REVIEWER),
        ("admin@agentsec.com", "Security Administrator", "AdminPass123!", UserRole.ADMIN),
        ("user@agentsec.com", "Standard User", "UserPass123!", UserRole.USER),
    ]
    created = []
    for email, name, pwd, role in demo_accounts:
        if not db.query(User).filter(User.email == email).first():
            new_u = User(
                email=email,
                full_name=name,
                password_hash=get_password_hash(pwd),
                role=role,
                is_active=True,
            )
            db.add(new_u)
            created.append({"email": email, "role": role.value, "default_password": pwd})
    db.commit()
    return {"message": "Demo accounts verified", "newly_created": created}
