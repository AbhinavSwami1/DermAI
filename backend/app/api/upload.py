from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.image_validation import (
    validate_image,
    ImageValidationError,
    MAX_FILE_SIZE,
)

router = APIRouter(prefix="/api/v1", tags=["Image Upload"])

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "original"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):

    try:
        # Read at most 10 MB + 1 byte to enforce the size limit.
        image_bytes = await file.read(MAX_FILE_SIZE + 1)

        metadata = validate_image(image_bytes)

        # Generate a safe internal filename.
        image_id = str(uuid4())
        extension = ".jpg" if metadata["format"] == "JPEG" else ".png"
        storage_filename = f"{image_id}{extension}"

        storage_path = STORAGE_DIR / storage_filename

        # Store the original validated image.
        storage_path.write_bytes(image_bytes)

        return {
            "message": "Image uploaded successfully.",
            "image_id": image_id,
            "status": "uploaded",
            "filename": file.filename,
            "storage_key": storage_filename,
            "image_metadata": metadata,
        }

    except ImageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except OSError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store uploaded image.",
        )

    finally:
        await file.close()