import math
from pathlib import Path
from typing import List, Set, Tuple

from PIL import Image

import re


# Common image formats that Pillow supports reliably for both reading and writing
SUPPORTED_EXTENSIONS: Set[str] = {
    "png",  # Portable Network Graphics
    "jpg",  # Joint Photographic Experts Group
    "jpeg",  # Joint Photographic Experts Group
    "bmp",  # Bitmap
    "gif",  # Graphics Interchange Format
    "tiff",  # Tagged Image File Format
    "webp",  # Web Picture format
}


def validate_extension(extension: str) -> str:
    """
    Validate and normalize the file extension.
    Returns normalized extension (lowercase, no leading dot).
    Raises ValueError if extension is not supported.
    """
    # Remove leading dot and convert to lowercase
    ext = extension.lstrip(".").lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format: {extension}\n"
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return ext


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
                min((row + 1) * slice_size, height),
            )
            slice_img = image.crop(box)

            # If this is an edge piece, create a full-sized slice with padding
            if slice_img.size != (slice_size, slice_size):
                padded = Image.new(image.mode, (slice_size, slice_size))
                padded.paste(slice_img, (0, 0))
                slice_img = padded

            slices.append(slice_img)

    return slices


def assemble_image(
    slice_dir: Path,
    rows: int,
    cols: int,
    prefix: str = "slice",
    extension: str = "png",
) -> Image.Image:
    """
    Assemble slices back into the original image.

    Args:
        slice_dir: Directory containing the slices
        rows: Number of rows in the original image grid
        cols: Number of columns in the original image grid
        prefix: Prefix used in slice filenames (default: "slice")
        extension: File extension for slice images (default: "png")

    Returns:
        Assembled PIL Image
    """
    # Load and sort slices
    slices = load_slices(slice_dir, prefix, extension)

    # Validate dimensions and get slice size
    slice_width, slice_height = validate_dimensions(slices, rows, cols)

    # Create new image
    width = cols * slice_width
    height = rows * slice_height
    assembled = Image.new("RGBA", (width, height))

    # Place slices
    for img, idx in slices:
        row = idx // cols
        col = idx % cols
        x = col * slice_width
        y = row * slice_height
        assembled.paste(img, (x, y))

    return assembled


def save_slices(
    slices: List[Image.Image], output_dir: Path, prefix: str = "slice"
) -> List[Path]:
    """Save slices to disk and return list of saved file paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    padding = len(str(len(slices)))

    for idx, slice_img in enumerate(slices):
        output_path = output_dir / f"{prefix}_{idx:0{padding}d}.png"
        slice_img.save(output_path)
        saved_paths.append(output_path)

    return saved_paths


def load_slices(
    slice_dir: Path, prefix: str = "slice", extension: str = "png"
) -> List[Tuple[Image.Image, int]]:
    """
    Load all slices from directory and return them sorted by index.
    Returns list of tuples (image, index).
    """
    if not isinstance(slice_dir, Path):
        raise TypeError("slice_dir must be a Path object")

    if not slice_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {slice_dir}")

    # Validate and normalize extension
    extension = validate_extension(extension)

    # Find all files with our naming pattern and specified extension
    slice_pattern = re.compile(rf"{prefix}_(\d+)\.{extension}$")
    slices = []

    for file_path in slice_dir.glob(f"*.{extension}"):
        match = slice_pattern.match(file_path.name)
        if match:
            try:
                idx = int(match.group(1))
                img = Image.open(file_path)
                slices.append((img, idx))
            except (ValueError, OSError) as e:
                raise ValueError(f"Failed to load slice {file_path}: {e}")

    if not slices:
        raise ValueError(f"No valid slices found in {slice_dir}")

    # Sort by index
    return sorted(slices, key=lambda x: x[1])


def validate_dimensions(
    slices: List[Tuple[Image.Image, int]], rows: int, cols: int
) -> Tuple[int, int]:
    """
    Validate slice dimensions and count against expected rows and columns.
    Returns tuple of (slice_width, slice_height).
    """
    if not slices:
        raise ValueError("No slices provided")

    expected_slices = rows * cols
    if len(slices) != expected_slices:
        raise ValueError(
            f"Expected {expected_slices} slices (rows={rows}, cols={cols}), but found {len(slices)}"
        )

    # Get dimensions from first slice
    first_slice = slices[0][0]
    slice_width, slice_height = first_slice.size

    # Validate all slices have the same dimensions
    for img, idx in slices:
        if img.size != (slice_width, slice_height):
            raise ValueError(
                f"Slice {idx} has inconsistent dimensions {img.size}, "
                f"expected ({slice_width}, {slice_height})"
            )

    return slice_width, slice_height
