from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Case, Image as ImageModel
from app.schemas import ImageResponse
from app.services.image_validation import (
    validate_image,
    ImageValidationError,
    MAX_FILE_SIZE,
)

router = APIRouter(prefix="/api/v1", tags=["Image Upload"])

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "original"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    case_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    storage_path = None

    try:
        existing_case = db.scalar(
            select(Case).where(Case.case_id == case_id)
        )

        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found.",
            )

        image_bytes = await file.read(MAX_FILE_SIZE + 1)
        metadata = validate_image(image_bytes)

        image_id = uuid4()
        extension = ".jpg" if metadata["format"] == "JPEG" else ".png"
        storage_filename = f"{image_id}{extension}"

        storage_path = STORAGE_DIR / storage_filename
        storage_path.write_bytes(image_bytes)

        new_image = ImageModel(
            image_id=image_id,
            case_id=case_id,
            original_filename=file.filename or "uploaded_image",
            mime_type=metadata["mime_type"],
            file_size_bytes=metadata["file_size_bytes"],
            storage_key=storage_filename,
            width=metadata["width"],
            height=metadata["height"],
        )

        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        return new_image

    except ImageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except (OSError, SQLAlchemyError):
        db.rollback()

        if storage_path and storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store image or save image metadata.",
        )

    finally:
        await file.close()