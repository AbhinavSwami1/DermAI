import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.models import RefreshToken


REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


def create_refresh_token(
    db: Session,
    user_id: UUID,
    family_id: UUID | None = None,
) -> tuple[str, RefreshToken]:
    """Generate and persist a hashed refresh token."""

    raw_token = generate_refresh_token()

    token_record = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        family_id=family_id or uuid4(),
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        ),
    )

    db.add(token_record)
    db.flush()

    return raw_token, token_record


def revoke_token_family(
    db: Session,
    family_id: UUID,
) -> None:
    """Revoke every refresh token belonging to a family."""

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )


def rotate_refresh_token(
    db: Session,
    raw_token: str,
) -> tuple[str, RefreshToken] | None:
    """Rotate a refresh token and detect reuse of revoked tokens."""

    token_hash = hash_refresh_token(raw_token)

    token_record = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .with_for_update()
    )

    if token_record is None:
        return None

    if token_record.revoked_at is not None:
        revoke_token_family(db, token_record.family_id)
        return None

    now = datetime.now(timezone.utc)

    if token_record.expires_at <= now:
        return None

    new_raw_token, new_record = create_refresh_token(
        db,
        user_id=token_record.user_id,
        family_id=token_record.family_id,
    )

    token_record.revoked_at = now
    token_record.replaced_by_token_id = new_record.token_id

    db.flush()

    return new_raw_token, new_record


def revoke_refresh_token(
    db: Session,
    raw_token: str,
) -> bool:
    """Revoke a single active refresh token."""

    token_record = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .with_for_update()
    )

    if token_record is None or token_record.revoked_at is not None:
        return False

    token_record.revoked_at = datetime.now(timezone.utc)
    db.flush()

    return True