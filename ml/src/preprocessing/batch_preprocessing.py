from pathlib import Path
import sys
import pandas as pd
from tqdm import tqdm

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

sys.path.insert(0, str(PROJECT_ROOT / "ml" / "src"))

from preprocessing.image_preprocessing import (
    load_image,
    resize_image
)


def process_dataset(
    metadata_path,
    image_directory,
    output_directory,
    image_size=224,
    max_images=None
):
    """
    Process dataset images and save resized RGB PNG files.
    Supports images stored inside multiple subfolders.
    """

    metadata_path = Path(metadata_path)
    image_directory = Path(image_directory)
    output_directory = Path(output_directory)

    output_directory.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(metadata_path)

    # Limit images during testing
    if max_images is not None:
        df = df.head(max_images)

    # Find images recursively in all subfolders
    image_index = {
        path.name: path
        for path in image_directory.rglob("*")
        if path.is_file()
    }

    successful = 0
    failed = []

    for _, row in tqdm(
        df.iterrows(),
        total=len(df),
        desc="Processing images"
    ):

        image_name = row["img_id"]
        image_path = image_index.get(image_name)
        output_path = output_directory / image_name

        try:
            if image_path is None:
                raise FileNotFoundError(
                    f"Image not found: {image_name}"
                )

            image = load_image(image_path)
            image = resize_image(image, (image_size, image_size))
            image.save(output_path, format="PNG")

            successful += 1

        except Exception as error:
            failed.append({
                "image": image_name,
                "error": str(error)
            })

    print("\nBATCH PREPROCESSING SUMMARY")
    print("Total images:", len(df))
    print("Successfully processed:", successful)
    print("Failed images:", len(failed))

    return {
        "total": len(df),
        "successful": successful,
        "failed": failed
    }