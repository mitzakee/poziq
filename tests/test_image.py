import math
import pytest
from pathlib import Path
from PIL import Image

from poziq import image
from .fixtures import sample_slices, invalid_size_slices, temp_dir, sample_image


class TestImageSlicing:
    """Test suite for image slicing functionality."""

    def test_slice_grid_mode(self, temp_dir, sample_image):
        """Test slicing in grid mode."""
        output_dir = temp_dir / "slices"
        slices = image.slice_image(sample_image, rows=2, cols=3)
        saved_paths = image.save_slices(slices, output_dir)

        assert len(slices) == 6  # 2x3 grid
        assert len(saved_paths) == 6
        assert all(isinstance(slice_img, Image.Image) for slice_img in slices)

        # Verify dimensions
        slice_width = 400 // 3  # Original width divided by cols
        slice_height = 300 // 2  # Original height divided by rows
        assert all(
            slice_img.size == (slice_width, slice_height) for slice_img in slices
        )

    def test_slice_dimensions_mode(self, temp_dir, sample_image):
        """Test slicing with explicit dimensions."""
        output_dir = temp_dir / "slices"
        slices = image.slice_image(sample_image, slice_width=100, slice_height=150)
        saved_paths = image.save_slices(slices, output_dir)

        expected_cols = math.ceil(400 / 100)  # Original width divided by slice width
        expected_rows = math.ceil(300 / 150)  # Original height divided by slice height
        expected_slices = expected_rows * expected_cols

        assert len(slices) == expected_slices
        assert all(slice_img.size == (100, 150) for slice_img in slices)

    def test_slice_mixed_parameters(self, temp_dir, sample_image):
        """Test slicing with mix of grid and dimension parameters."""
        output_dir = temp_dir / "slices"
        # Using slice_width with rows
        slices = image.slice_image(sample_image, slice_width=100, rows=2)
        assert all(slice_img.size[0] == 100 for slice_img in slices)

        # Using slice_height with cols
        slices = image.slice_image(sample_image, slice_height=150, cols=3)
        assert all(slice_img.size[1] == 150 for slice_img in slices)

    def test_slice_edge_pieces(self, temp_dir, sample_image):
        """Test that edge pieces are properly padded when needed."""
        # Create uneven slices to force edge padding
        slices = image.slice_image(sample_image, slice_width=150, slice_height=125)

        # All slices should have the same dimensions, even edge pieces
        slice_size = (150, 125)
        assert all(slice_img.size == slice_size for slice_img in slices)

    @pytest.mark.parametrize(
        "invalid_params",
        [
            {"rows": 0, "cols": 3},
            {"rows": -1, "cols": 3},
            {"rows": 2, "cols": 0},
            {"slice_width": 0, "slice_height": 100},
            {"slice_width": 100, "slice_height": 0},
            {"slice_width": -100, "slice_height": 100},
        ],
    )
    def test_invalid_parameters(self, sample_image, invalid_params):
        """Test handling of invalid slicing parameters."""
        with pytest.raises((ValueError, TypeError)):
            image.slice_image(sample_image, **invalid_params)

    def test_oversized_dimensions(self, sample_image):
        """Test handling of slice dimensions larger than image."""
        with pytest.raises(
            ValueError, match="slice dimensions cannot be larger than image dimensions"
        ):
            image.slice_image(sample_image, slice_width=500, slice_height=100)

        with pytest.raises(
            ValueError, match="slice dimensions cannot be larger than image dimensions"
        ):
            image.slice_image(sample_image, slice_width=100, slice_height=400)

    def test_too_many_divisions(self, sample_image):
        """Test handling of too many rows/columns for image size."""
        with pytest.raises(ValueError, match="Image dimensions .* are too small"):
            image.slice_image(sample_image, rows=1000, cols=2)


class TestImageAssembly:
    """Test suite for image assembly functionality."""

    def test_load_slices_success(self, temp_dir, sample_slices):
        """Test successful loading of image slices."""
        slices = image._load_slices(temp_dir)
        assert len(slices) == 4
        assert all(isinstance(img, Image.Image) for img, _ in slices)
        assert [idx for _, idx in slices] == [0, 1, 2, 3]

    def test_load_slices_empty_directory(self, temp_dir):
        """Test loading from empty directory."""
        with pytest.raises(ValueError, match="No valid slices found"):
            image._load_slices(temp_dir)

    def test_load_slices_invalid_directory(self):
        """Test loading from non-existent directory."""
        with pytest.raises(NotADirectoryError):
            image._load_slices(Path("nonexistent"))

    def test_validate_dimensions_success(self, temp_dir, sample_slices):
        """Test successful dimension validation."""
        slices = image._load_slices(temp_dir)
        width, height = image._validate_dimensions(slices, rows=2, cols=2)
        assert width == 100
        assert height == 150

    def test_validate_dimensions_wrong_count(self, temp_dir, sample_slices):
        """Test dimension validation with incorrect slice count."""
        slices = image._load_slices(temp_dir)
        with pytest.raises(ValueError, match="Expected .* slices"):
            image._validate_dimensions(slices, rows=2, cols=3)

    def test_validate_dimensions_inconsistent_size(self, temp_dir, invalid_size_slices):
        """Test dimension validation with inconsistent slice sizes."""
        slices = image._load_slices(temp_dir)
        with pytest.raises(ValueError, match="Slice .* has inconsistent dimensions"):
            image._validate_dimensions(slices, rows=2, cols=2)

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
