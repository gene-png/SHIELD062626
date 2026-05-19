"""FastAPI dependencies: current user resolution.

`current_user` reads the `Authorization: Bearer <token>` header, verifies the
access token, and loads the User row. Routes that don't need the user but
need the role take `require_role` instead (Phase 1 stage 7).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.jwt import TokenError, verify_token


def _bearer_token_from(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth.split(" ", 1)[1].strip()


def current_user(
    request: Request,
    db: Session = Depends(get_db),  # noqa: B008 - FastAPI dependency-injection idiom
) -> User:
    token = _bearer_token_from(request)
    try:
        payload = verify_token(token, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is no longer active.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
