from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -------------------------
# USER SCHEMAS
# -------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime


# -------------------------
# CASE SCHEMAS
# -------------------------

class CaseCreate(BaseModel):
    owner_id: UUID


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    image_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    storage_key: str
    width: int | None
    height: int | None
    uploaded_at: datetime