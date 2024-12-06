import math
from pathlib import Path
from typing import List

from PIL import Image


def slice_image(image_path: Path, slice_size: int) -> List[Image.Image]:
    """
    Slice the image into squares of specified size.
    Returns list of PIL Image objects.

    Args:
        image_path: Path to the image file
        slice_size: Size of each square slice in pixels

    Raises:
        ValueError: If slice_size is invalid or image is too small
        FileNotFoundError: If image_path doesn't exist
        OSError: If file is not a valid image
    """
    # Validate inputs
    if not isinstance(image_path, Path):
        raise TypeError("image_path must be a Path object")

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if not isinstance(slice_size, int):
        raise TypeError("slice_size must be an integer")

    if slice_size <= 0:
        raise ValueError("slice_size must be positive")

    # Open and validate image
    try:
        image = Image.open(image_path)
    except OSError as e:
        raise OSError(f"Failed to open image: {e}")

    width, height = image.size
    if width < slice_size or height < slice_size:
        raise ValueError(
            f"Image dimensions ({width}x{height}) are smaller than "
            f"slice_size ({slice_size}x{slice_size})"
        )

    rows = math.ceil(height / slice_size)
    cols = math.ceil(width / slice_size)

    slices = []
    for row in range(rows):
        for col in range(cols):
            box = (
                col * slice_size,
                row * slice_size,
                min((col + 1) * slice_size, width),
                min((row + 1) * slice_size, height)
            )
            slice_img = image.crop(box)

            # If this is an edge piece, create a full-sized slice with padding
            if slice_img.size != (slice_size, slice_size):
                padded = Image.new(image.mode, (slice_size, slice_size))
                padded.paste(slice_img, (0, 0))
                slice_img = padded

            slices.append(slice_img)

    return slices
