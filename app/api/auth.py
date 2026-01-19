from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import authenticate_user, create_token, get_current_user, verify_token
from app.config import settings
from app.schemas.auth import (
    RefreshTokenRequest,
    Token,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = create_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires,
        token_type="access",
    )
    refresh_token = create_token(
        data={"sub": form_data.username},
        expires_delta=refresh_token_expires,
        token_type="refresh",
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_request: RefreshTokenRequest):
    try:
        token_data = verify_token(token_request.refresh_token, "refresh")
        username = token_data.username
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_token(
        data={"sub": username},
        expires_delta=access_token_expires,
        token_type="access",
    )

    return Token(
        access_token=new_access_token,
        refresh_token=token_request.refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: str = Depends(get_current_user)):
    return UserResponse(username=current_user)
