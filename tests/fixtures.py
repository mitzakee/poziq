import pytest
import tempfile
from pathlib import Path
from PIL import Image


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample image for slicing tests."""
    # Create test image with a gradient pattern for easy visual verification
    width, height = 400, 300
    image = Image.new("RGBA", (width, height))

    # Create a simple gradient pattern
    pixels = []
    for y in range(height):
        for x in range(width):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = 100
            pixels.append((r, g, b, 255))

    image.putdata(pixels)
    image_path = temp_dir / "test_image.png"
    image.save(image_path)
    return image_path


@pytest.fixture
def sample_slices(temp_dir):
    """Create sample image slices for testing."""
    # Create test slices with different colors
    slice_width, slice_height = 100, 150  # Using rectangular slices
    colors = [
        (255, 0, 0, 255),  # Red
        (0, 255, 0, 255),  # Green
        (0, 0, 255, 255),  # Blue
        (255, 255, 0, 255),  # Yellow
    ]

    slices = []
    for idx, color in enumerate(colors):
        img = Image.new("RGBA", (slice_width, slice_height), color)
        path = temp_dir / f"slice_{idx}.png"
        img.save(path)
        slices.append(path)

    return slices


@pytest.fixture
def invalid_size_slices(temp_dir):
    """Create sample slices with inconsistent sizes."""
    sizes = [
        (100, 150),
        (100, 150),
        (90, 150),  # <- slice has different width
        (100, 150),
    ]
    colors = [
        (255, 0, 0, 255),  # Red
        (0, 255, 0, 255),  # Green
        (0, 0, 255, 255),  # Blue
        (255, 255, 0, 255),  # Yellow
    ]
    slices = []
    for idx, (size, color) in enumerate(zip(sizes, colors)):
        img = Image.new("RGBA", size, color)
        path = temp_dir / f"slice_{idx}.png"
        img.save(path)
        slices.append(path)

    return slices
