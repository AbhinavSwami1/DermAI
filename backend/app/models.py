import uuid

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# -------------------------
# USERS
# -------------------------

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    cases: Mapped[list["Case"]] = relationship(
        back_populates="owner"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user"
    )


# -------------------------
# ROLES
# -------------------------

class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role_name: Mapped[str] = mapped_column(
        String(60), unique=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        back_populates="role"
    )


# -------------------------
# USER ROLES
# -------------------------

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.role_id"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates="user_roles"
    )
    role: Mapped["Role"] = relationship(
        back_populates="user_roles"
    )


# -------------------------
# CASES
# -------------------------

class Case(Base):
    __tablename__ = "cases"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40), default="created", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped["User"] = relationship(
        back_populates="cases"
    )
    images: Mapped[list["Image"]] = relationship(
        back_populates="case"
    )


# -------------------------
# IMAGES
# -------------------------

class Image(Base):
    __tablename__ = "images"

    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.case_id"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    storage_key: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )
    width: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    height: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    case: Mapped["Case"] = relationship(
        back_populates="images"
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="image"
    )


# -------------------------
# MODEL VERSIONS
# -------------------------

class ModelVersion(Base):
    __tablename__ = "model_versions"

    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    version: Mapped[str] = mapped_column(
        String(60), nullable=False
    )
    architecture: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    checkpoint_reference: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="model_version"
    )


# -------------------------
# PREDICTIONS
# -------------------------

class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.image_id"),
        nullable=False,
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.model_version_id"),
        nullable=False,
    )
    predicted_label: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    class_scores: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    image: Mapped["Image"] = relationship(
        back_populates="predictions"
    )
    model_version: Mapped["ModelVersion"] = relationship(
        back_populates="predictions"
    )