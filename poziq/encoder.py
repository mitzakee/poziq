from pathlib import Path
from typing import Union, List, Tuple
from PIL import Image
import re

SUPPORTED_FORMATS = {"rgb", "hex"}


class EncodingError(Exception):
    """Custom exception for encoding/decoding errors."""

    pass


def encode_image(image_path: Union[str, Path], format: str = "rgb") -> str:
    """
    Encode an image file into a text representation.

    Args:
        image_path: Path to the image file
        format: 'rgb' or 'hex' for color format

    Returns:
        String representation of the image

    Raises:
        EncodingError: If the format is invalid or image cannot be processed
    """
    if format not in SUPPORTED_FORMATS:
        raise EncodingError(
            f"Invalid format: {format}. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    try:
        img = Image.open(image_path)
        width, height = img.size

        # Convert to RGB mode if not already
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Get pixel data
        pixels = []
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                if format == "hex":
                    pixels.append(f"{r:02x}{g:02x}{b:02x}")
                else:  # rgb format
                    pixels.append(f"{r},{g},{b}")

        # Create the encoded string
        header = f"{width},{height},{format}"
        pixel_data = ";".join(pixels)

        return f"{header}:{pixel_data}"

    except (OSError, IOError) as e:
        raise EncodingError(f"Failed to open or process image: {str(e)}")
    except Exception as e:
        raise EncodingError(f"Unexpected error while encoding image: {str(e)}")


def decode_image(encoded_str: str) -> Image.Image:
    """
    Decode a text representation back into an image.

    Args:
        encoded_str: The encoded string representation

    Returns:
        PIL Image object

    Raises:
        EncodingError: If the string format is invalid or cannot be decoded
    """
    if not isinstance(encoded_str, str):
        raise EncodingError("Input must be a string")

    if not encoded_str:
        raise EncodingError("Empty input string")

    try:
        # Split header and data
        if ":" not in encoded_str:
            raise EncodingError("Invalid format: missing header separator ':'")

        header, pixel_data = encoded_str.split(":", 1)

        # Parse header
        try:
            header_parts = header.split(",")
            if len(header_parts) != 3:
                raise EncodingError("Invalid header format")

            width, height, format = header_parts
            width = int(width)
            height = int(height)

            if width <= 0 or height <= 0:
                raise EncodingError("Invalid dimensions: must be positive")

            if format not in SUPPORTED_FORMATS:
                raise EncodingError(f"Invalid format: {format}")
        except ValueError:
            raise EncodingError("Invalid header: dimensions must be integers")

        # Split pixel data
        pixels = pixel_data.split(";")
        expected_pixels = width * height
        if len(pixels) != expected_pixels:
            raise EncodingError(
                f"Invalid pixel count: expected {expected_pixels}, got {len(pixels)}"
            )

        # Create new image
        img = Image.new("RGB", (width, height))

        # Parse and validate pixels
        for i, pixel in enumerate(pixels):
            x, y = i % width, i // width

            if format == "hex":
                if not re.match(r"^[0-9a-fA-F]{6}$", pixel):
                    raise EncodingError(
                        f"Invalid hex color format at position {i}: {pixel}"
                    )
                try:
                    r = int(pixel[0:2], 16)
                    g = int(pixel[2:4], 16)
                    b = int(pixel[4:6], 16)
                except ValueError:
                    raise EncodingError(
                        f"Invalid hex color values at position {i}: {pixel}"
                    )
            else:  # rgb format
                try:
                    r, g, b = map(int, pixel.split(","))
                    if not all(0 <= c <= 255 for c in (r, g, b)):
                        raise EncodingError(
                            f"Invalid RGB values must be between 0 and 255 at position {i}"
                        )
                except ValueError:
                    raise EncodingError(
                        f"Invalid RGB color format at position {i}: {pixel}"
                    )

            img.putpixel((x, y), (r, g, b))

        return img

    except EncodingError:
        raise
    except Exception as e:
        raise EncodingError(f"Unexpected error while decoding: {str(e)}")


def encode_images(
    image_paths: List[Union[str, Path]], format: str = "rgb"
) -> List[Tuple[Path, Union[str, EncodingError]]]:
    """
    Encode multiple images at once.

    Args:
        image_paths: List of paths to image files
        format: 'rgb' or 'hex' for color format

    Returns:
        List of tuples containing (path, encoded_string) for successful encodings
        or (path, EncodingError) for failed encodings

    Raises:
        ValueError: If format is invalid or no valid paths provided
        TypeError: If image_paths is not a list or paths are not str/Path
    """
    # Validate inputs
    if not isinstance(image_paths, (list, tuple)):
        raise TypeError("image_paths must be a list or tuple")

    if not image_paths:
        raise ValueError("No image paths provided")

    if format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Invalid format: {format}. Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    # Convert all paths to Path objects and validate
    try:
        paths = [Path(p) for p in image_paths]
    except TypeError:
        raise TypeError("All paths must be string or Path objects")

    # Process images
    results = []
    for path in paths:
        try:
            # Basic path validation
            if not isinstance(path, Path):
                raise TypeError(f"Invalid path type: {type(path)}")

            if not path.is_file():
                raise EncodingError(f"File not found: {path}")

            # Try to encode
            encoded = encode_image(path, format)
            results.append((path, encoded))

        except EncodingError as e:
            # Pass through encoding-specific errors
            results.append((path, e))
        except Exception as e:
            # Wrap unexpected errors
            results.append((path, EncodingError(f"Unexpected error: {str(e)}")))

    return results


def decode_images(
    encoded_data: List[Tuple[Union[str, Path], str]], output_dir: Union[str, Path]
) -> List[Tuple[str, Union[Path, EncodingError]]]:
    """
    Decode multiple encoded strings to images.

    Args:
        encoded_data: List of tuples containing (output_filename, encoded_string)
        output_dir: Directory to save decoded images

    Returns:
        List of tuples containing (original_name, output_path) for successful decodings
        or (original_name, EncodingError) for failed decodings

    Raises:
        ValueError: If no valid encoded data provided
        TypeError: If inputs are of wrong type
        OSError: If output directory cannot be created
    """
    if not isinstance(encoded_data, (list, tuple)):
        raise TypeError("encoded_data must be a list or tuple")

    if not encoded_data:
        raise ValueError("No encoded data provided")

    try:
        output_dir = Path(output_dir)
    except TypeError:
        raise TypeError("output_dir must be a string or Path object")

    # Create output directory
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise OSError(f"Failed to create output directory: {str(e)}")

    results = []
    for name, encoded_str in encoded_data:
        try:
            # Validate name
            if not isinstance(name, (str, Path)):
                raise TypeError(f"Invalid filename type: {type(name)}")

            name = str(name)  # Convert Path to string if necessary

            # Validate encoded string
            if not isinstance(encoded_str, str):
                raise EncodingError("Encoded data must be a string")

            # Decode the image
            img = decode_image(encoded_str)

            # Save the result
            output_path = output_dir / f"{Path(name).stem}.png"
            img.save(output_path)
            results.append((name, output_path))

        except (EncodingError, TypeError) as e:
            results.append((name, e))
        except Exception as e:
            results.append((name, EncodingError(f"Unexpected error: {str(e)}")))

    return results
