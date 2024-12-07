import pytest
from pathlib import Path
from PIL import Image
import tempfile

from poziq import image


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


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


class TestImageAssembly:
    """Test suite for image assembly functionality."""

    def test_load_slices_success(self, temp_dir, sample_slices):
        """Test successful loading of image slices."""
        slices = image.load_slices(temp_dir)
        assert len(slices) == 4
        assert all(isinstance(img, Image.Image) for img, _ in slices)
        assert [idx for _, idx in slices] == [0, 1, 2, 3]

    def test_load_slices_empty_directory(self, temp_dir):
        """Test loading from empty directory."""
        with pytest.raises(ValueError, match="No valid slices found"):
            image.load_slices(temp_dir)

    def test_load_slices_invalid_directory(self):
        """Test loading from non-existent directory."""
        with pytest.raises(NotADirectoryError):
            image.load_slices(Path("nonexistent"))

    def test_validate_dimensions_success(self, temp_dir, sample_slices):
        """Test successful dimension validation."""
        slices = image.load_slices(temp_dir)
        width, height = image.validate_dimensions(slices, rows=2, cols=2)
        assert width == 100
        assert height == 150

    def test_validate_dimensions_wrong_count(self, temp_dir, sample_slices):
        """Test dimension validation with incorrect slice count."""
        slices = image.load_slices(temp_dir)
        with pytest.raises(ValueError, match="Expected .* slices"):
            image.validate_dimensions(slices, rows=2, cols=3)

    def test_validate_dimensions_inconsistent_size(self, temp_dir, invalid_size_slices):
        """Test dimension validation with inconsistent slice sizes."""
        slices = image.load_slices(temp_dir)
        with pytest.raises(ValueError, match="Slice .* has inconsistent dimensions"):
            image.validate_dimensions(slices, rows=2, cols=2)

    def test_assemble_image_success(self, temp_dir, sample_slices):
        """Test successful image assembly."""
        assembled = image.assemble_image(temp_dir, rows=2, cols=2)
        assert isinstance(assembled, Image.Image)
        assert assembled.size == (200, 300)  # 2x2 grid of 100x150 slices

    def test_assemble_image_different_prefix(self, temp_dir, sample_slices):
        """Test assembly with custom prefix."""
        # Rename files to use different prefix
        for path in sample_slices:
            new_name = path.parent / path.name.replace("slice", "custom")
            path.rename(new_name)

        assembled = image.assemble_image(temp_dir, rows=2, cols=2, prefix="custom")
        assert isinstance(assembled, Image.Image)
        assert assembled.size == (200, 300)

    def test_assemble_image_different_extension(self, temp_dir, sample_slices):
        """Test assembly with different image format."""
        # Convert files to JPEG
        for path in sample_slices:
            img = Image.open(path)
            jpg_path = path.with_suffix(".jpg")
            img.convert("RGB").save(jpg_path)  # JPEG doesn't support RGBA
            path.unlink()

        assembled = image.assemble_image(temp_dir, rows=2, cols=2, extension="jpg")
        assert isinstance(assembled, Image.Image)
        assert assembled.size == (200, 300)

    @pytest.mark.parametrize(
        "extension",
        [
            "txt",
            "invalid",
            "doc",
            "",
        ],
    )
    def test_invalid_extension(self, extension):
        """Test validation of invalid file extensions."""
        with pytest.raises(ValueError, match="Unsupported image format"):
            image.validate_extension(extension)

    @pytest.mark.parametrize("extension", list(image.SUPPORTED_EXTENSIONS))
    def test_valid_extension(self, extension):
        """Test validation of all supported extensions."""
        validated = image.validate_extension(extension)
        assert validated == extension.lower()
        assert validated == image.validate_extension(
            f".{extension}"
        )  # Test with leading dot
