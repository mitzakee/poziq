from enum import Enum, auto
import math
from pathlib import Path
from typing import List, Set, Tuple, Union

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


class SliceMode(Enum):
    """Enum representing the different modes of slicing an image."""

    GRID = auto()  # Using rows and columns
    DIMENSIONS = auto()  # Using explicit slice dimensions


def slice_image(
    image_path: Path,
    rows: Union[int, None] = None,
    cols: Union[int, None] = None,
    slice_width: Union[int, None] = None,
    slice_height: Union[int, None] = None,
) -> List[Image.Image]:
    """
    Slice the image into a grid. Can be specified either by grid dimensions (rows x cols)
    or slice dimensions (width x height). If both are provided, slice dimensions take priority.

    Args:
        image_path: Path to the image file
        rows: Number of rows to slice into (used if slice dimensions not provided)
        cols: Number of columns to slice into (used if slice dimensions not provided)
        slice_width: Width of each slice in pixels (takes priority over cols)
        slice_height: Height of each slice in pixels (takes priority over rows)

    Returns:
        List of PIL Image slices
    """
    # Validate image path
    _validate_image_path(image_path)

    # Open image
    try:
        image = Image.open(image_path)
    except OSError as e:
        raise OSError(f"Failed to open image: {e}")

    # Calculate dimensions
    slice_width, slice_height, rows, cols = _calculate_slice_dimensions(
        image.size, rows, cols, slice_width, slice_height
    )

    # Create slices
    slices = []
    for row in range(rows):
        for col in range(cols):
            slice_img = _create_slice(
                image,
                row,
                col,
                slice_width,
                slice_height,
                is_last_col=(col == cols - 1),
                is_last_row=(row == rows - 1),
            )
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
    slices = _load_slices(slice_dir, prefix, extension)

    # Validate dimensions and get slice size
    slice_width, slice_height = _validate_dimensions(slices, rows, cols)

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
    slices: List[Image.Image],
    output_dir: Path,
    prefix: str = "slice",
    extension: str = "png",
) -> List[Path]:
    """Save slices to disk and return list of saved file paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    padding = len(str(len(slices)))

    for idx, slice_img in enumerate(slices):
        output_path = output_dir / f"{prefix}_{idx:0{padding}d}.{extension}"
        slice_img.save(output_path)
        saved_paths.append(output_path)

    return saved_paths


def _calculate_slice_dimensions(
    image_size: tuple[int, int],
    rows: Union[int, None],
    cols: Union[int, None],
    slice_width: Union[int, None],
    slice_height: Union[int, None],
) -> tuple[int, int, int, int]:
    """
    Calculate the final slice dimensions and grid size based on input parameters.
    Returns tuple of (slice_width, slice_height, rows, cols).
    """
    width, height = image_size
    mode = _validate_slice_parameters(rows, cols, slice_width, slice_height)

    if mode == SliceMode.DIMENSIONS:
        # Calculate missing slice dimensions from grid if provided
        if slice_width is None:
            if cols is None:
                raise ValueError(
                    "Must provide slice_width or cols when using slice dimensions"
                )
            slice_width = width // cols
        if slice_height is None:
            if rows is None:
                raise ValueError(
                    "Must provide slice_height or rows when using slice dimensions"
                )
            slice_height = height // rows

        # Validate dimensions
        if not isinstance(slice_width, int) or not isinstance(slice_height, int):
            raise TypeError("slice dimensions must be integers")
        if slice_width <= 0 or slice_height <= 0:
            raise ValueError("slice dimensions must be positive")
        if slice_width > width or slice_height > height:
            raise ValueError("slice dimensions cannot be larger than image dimensions")

        # Calculate grid size from dimensions
        cols = math.ceil(width / slice_width)
        rows = math.ceil(height / slice_height)
    else:  # SliceMode.GRID
        # Using grid specifications
        if not isinstance(rows, int) or not isinstance(cols, int):
            raise TypeError("rows and cols must be integers")
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")

        # Calculate slice dimensions from grid
        slice_width = width // cols
        slice_height = height // rows

        if slice_width == 0 or slice_height == 0:
            raise ValueError(
                f"Image dimensions ({width}x{height}) are too small "
                f"for the specified grid ({rows}x{cols})"
            )

    return slice_width, slice_height, rows, cols


def _validate_slice_parameters(
    rows: Union[int, None],
    cols: Union[int, None],
    slice_width: Union[int, None],
    slice_height: Union[int, None],
) -> SliceMode:
    """
    Validate the slicing parameters and determine which mode to use.
    Returns the appropriate SliceMode.

    Raises:
        ValueError: If neither grid nor dimensions parameters are properly specified
    """
    using_dimensions = slice_width is not None or slice_height is not None
    using_grid = rows is not None and cols is not None

    if not (using_dimensions or using_grid):
        raise ValueError(
            "Must specify either (rows and cols) or (slice_width and/or slice_height)"
        )

    # Dimensions take priority if both are specified
    return SliceMode.DIMENSIONS if using_dimensions else SliceMode.GRID


def _create_slice(
    image: Image.Image,
    row: int,
    col: int,
    slice_width: int,
    slice_height: int,
    is_last_col: bool,
    is_last_row: bool,
) -> Image.Image:
    """Create a single slice from the image with proper padding if needed."""
    # Calculate boundaries for this slice
    left = col * slice_width
    top = row * slice_height
    right = left + slice_width if not is_last_col else image.size[0]
    bottom = top + slice_height if not is_last_row else image.size[1]

    # Crop the slice
    slice_img = image.crop((left, top, right, bottom))

    # If this is an edge piece and has different dimensions, create a standard-sized slice
    if (is_last_col or is_last_row) and slice_img.size != (slice_width, slice_height):
        padded = Image.new(image.mode, (slice_width, slice_height))
        padded.paste(slice_img, (0, 0))
        slice_img = padded

    return slice_img


def _load_slices(
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


def _validate_dimensions(
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


def _validate_image_path(image_path: Path) -> None:
    """Validate the image path exists and is the correct type."""
    if not isinstance(image_path, Path):
        raise TypeError("image_path must be a Path object")

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
