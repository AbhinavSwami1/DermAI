import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import verify_password
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.services.refresh_token_service import (
    create_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token,
)


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# REFRESH TOKEN COOKIE CONFIGURATION

REFRESH_COOKIE_NAME = "dermai_refresh_token"

REFRESH_COOKIE_SECURE = (
    os.getenv("REFRESH_COOKIE_SECURE", "false").lower() == "true"
)

REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


def set_refresh_cookie(response: Response, token: str) -> None:
    """Set the refresh token in an HttpOnly cookie."""

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_TOKEN_MAX_AGE,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        secure=REFRESH_COOKIE_SECURE,
        samesite="lax",
    )


# LOGIN

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == credentials.email)
    )

    if not user or not verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    try:
        access_token = create_access_token(user.user_id)

        refresh_token, _ = create_refresh_token(
            db=db,
            user_id=user.user_id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    set_refresh_cookie(response, refresh_token)

    return TokenResponse(access_token=access_token)


# REFRESH ACCESS TOKEN

@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing.",
        )

    try:
        result = rotate_refresh_token(db, raw_token)

        if result is None:
            # Persist family revocation when a revoked token is reused.
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked refresh token.",
            )

        new_refresh_token, token_record = result

        user = db.get(User, token_record.user_id)

        if user is None or not user.is_active:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is unavailable.",
            )

        access_token = create_access_token(user.user_id)

        db.commit()

    except HTTPException:
        raise

    except Exception:
        db.rollback()
        raise

    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(access_token=access_token)


# LOGOUT

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)

    try:
        if raw_token:
            revoke_refresh_token(db, raw_token)
            db.commit()

    except Exception:
        db.rollback()
        raise

    clear_refresh_cookie(response)

    return {
        "message": "Logged out successfully."
    }