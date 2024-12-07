import pytest
from pathlib import Path
from PIL import Image

from poziq import encoder
from .fixtures import temp_dir, sample_image, runner


class TestImageEncoding:
    """Test suite for image encoding functionality."""

    def test_encode_rgb_format(self, sample_image):
        """Test encoding in RGB format."""
        encoded = encoder.encode_image(sample_image, format="rgb")

        # Verify header format
        header, data = encoded.split(":")
        width, height, format_type = header.split(",")
        assert format_type == "rgb"
        assert width == "400"
        assert height == "300"

        # Verify pixel data format
        pixels = data.split(";")
        assert len(pixels) == 400 * 300  # Total number of pixels
        # Check format of first pixel (should be r,g,b)
        r, g, b = map(int, pixels[0].split(","))
        assert all(0 <= c <= 255 for c in (r, g, b))

    def test_encode_hex_format(self, sample_image):
        """Test encoding in hex format."""
        encoded = encoder.encode_image(sample_image, format="hex")

        # Verify header format
        header, data = encoded.split(":")
        width, height, format_type = header.split(",")
        assert format_type == "hex"

        # Verify pixel data format
        pixels = data.split(";")
        assert len(pixels) == 400 * 300
        # Check format of first pixel (should be RRGGBB)
        assert len(pixels[0]) == 6
        assert all(c in "0123456789abcdef" for c in pixels[0].lower())

    def test_encode_decode_cycle(self, sample_image):
        """Test that encoding and decoding preserves image data."""
        for format in ["rgb", "hex"]:
            # Encode the image
            encoded = encoder.encode_image(sample_image, format=format)

            # Decode back to image
            decoded = encoder.decode_image(encoded)

            # Compare with original
            original = Image.open(sample_image)
            assert decoded.size == original.size

            # Compare a few sample pixels
            for x in [0, 200, 399]:
                for y in [0, 150, 299]:
                    assert decoded.getpixel((x, y)) == original.convert("RGB").getpixel(
                        (x, y)
                    )

    def test_encode_images_invalid_format(self, temp_dir, sample_image):
        """Test batch encoding with invalid format."""
        with pytest.raises(ValueError, match="Invalid format"):
            encoder.encode_images([sample_image], format="invalid")

    def test_encode_images_empty_list(self):
        """Test batch encoding with empty list."""
        with pytest.raises(ValueError, match="No image paths provided"):
            encoder.encode_images([])

    def test_encode_images_invalid_path_type(self, sample_image):
        """Test batch encoding with invalid path type."""
        with pytest.raises(TypeError):
            encoder.encode_images([sample_image, 123])

    def test_encode_images_nonexistent_file(self, temp_dir, sample_image):
        """Test batch encoding with nonexistent file."""
        nonexistent = temp_dir / "nonexistent.png"
        results = encoder.encode_images([sample_image, nonexistent])

        assert len(results) == 2
        assert isinstance(results[0][1], str)  # Success for valid image
        assert isinstance(
            results[1][1], encoder.EncodingError
        )  # Error for invalid path

    def test_encode_images_invalid_image(self, temp_dir, sample_image):
        """Test batch encoding with invalid image file."""
        invalid_image = temp_dir / "invalid.png"
        invalid_image.write_text("not an image")

        results = encoder.encode_images([sample_image, invalid_image])

        assert len(results) == 2
        assert isinstance(results[0][1], str)  # Success for valid image
        assert isinstance(
            results[1][1], encoder.EncodingError
        )  # Error for invalid image

    def test_encode_images_mixed_modes(self, temp_dir, sample_image):
        """Test batch encoding with images in different color modes."""
        # Create an L (grayscale) mode image
        gray_image = temp_dir / "gray.png"
        Image.new("L", (100, 100), color=128).save(gray_image)

        results = encoder.encode_images([sample_image, gray_image])

        assert len(results) == 2
        assert all(isinstance(r[1], str) for r in results)  # Both should succeed

        # Verify both encoded strings are in RGB format
        for _, encoded in results:
            header, _ = encoded.split(":")
            _, _, format_type = header.split(",")
            assert format_type in ["rgb", "hex"]

    def test_encode_images_success_all_formats(self, temp_dir, sample_image):
        """Test successful batch encoding in all supported formats."""
        for format in encoder.SUPPORTED_FORMATS:
            results = encoder.encode_images([sample_image], format=format)

            assert len(results) == 1
            assert isinstance(results[0][1], str)
            header, _ = results[0][1].split(":")
            _, _, format_type = header.split(",")
            assert format_type == format

    def test_invalid_encoded_string(self):
        """Test decoding with various invalid encoded strings."""
        invalid_strings = [
            "invalid",
            "2,2,rgb:invalid",
            "2,2,hex:invalid",
            "2,2,rgb:255,0",  # incomplete pixel data
            "2,2,hex:ff00",  # incomplete hex code
            "-1,2,rgb:0,0,0",  # invalid dimensions
            "2,2,rgb:256,0,0",  # invalid RGB values
            "2,2,hex:fffffg",  # invalid hex characters
        ]

        for invalid_str in invalid_strings:
            with pytest.raises(encoder.EncodingError):
                encoder.decode_image(invalid_str)


class TestImageDecoding:
    """Test suite for image decoding functionality."""

    @pytest.fixture
    def encoded_rgb(self):
        """Sample RGB encoded string."""
        return "2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255"

    @pytest.fixture
    def encoded_hex(self):
        """Sample hex encoded string."""
        return "2,2,hex:ff0000;00ff00;0000ff;ffffff"

    def test_decode_empty_string(self):
        """Test decoding empty string."""
        with pytest.raises(encoder.EncodingError, match="Empty input"):
            encoder.decode_image("")

    def test_decode_invalid_type(self):
        """Test decoding with invalid input type."""
        with pytest.raises(encoder.EncodingError, match="must be a string"):
            encoder.decode_image(123)

    def test_decode_missing_separator(self):
        """Test decoding string without header separator."""
        with pytest.raises(encoder.EncodingError, match="missing header separator"):
            encoder.decode_image("2,2,rgbdata")

    def test_decode_invalid_header_format(self):
        """Test decoding with invalid header format."""
        invalid_headers = [
            "2,rgb:data",  # Missing height
            "2,2:data",  # Missing format
            "a,2,rgb:data",  # Non-integer dimension
        ]
        for invalid in invalid_headers:
            with pytest.raises(encoder.EncodingError, match="Invalid header"):
                encoder.decode_image(invalid)

    def test_decode_invalid_dimensions(self):
        """Test decoding with invalid dimensions."""
        invalid_dims = [
            "0,2,rgb:data",
            "2,0,rgb:data",
            "-1,2,rgb:data",
            "2,-1,rgb:data",
        ]
        for invalid in invalid_dims:
            with pytest.raises(encoder.EncodingError, match="Invalid dimensions"):
                encoder.decode_image(invalid)

    def test_decode_invalid_pixel_count(self):
        """Test decoding with wrong number of pixels."""
        with pytest.raises(encoder.EncodingError, match="Invalid pixel count"):
            encoder.decode_image("2,2,rgb:255,0,0;0,255,0;0,0,255")  # Missing one pixel

    def test_decode_invalid_rgb_format(self, encoded_rgb):
        """Test decoding with invalid RGB values."""
        invalid_rgb = [
            "2,2,rgb:256,0,0;0,0,0;0,0,0;0,0,0",  # Value > 255
            "2,2,rgb:a,0,0;0,0,0;0,0,0;0,0,0",  # Non-numeric
            "2,2,rgb:0,0;0,0,0;0,0,0;0,0,0",  # Missing value
        ]
        for invalid in invalid_rgb:
            with pytest.raises(encoder.EncodingError, match="Invalid RGB"):
                encoder.decode_image(invalid)

    def test_decode_invalid_hex_format(self, encoded_hex):
        """Test decoding with invalid hex values."""
        invalid_hex = [
            "2,2,hex:fg0000;00ff00;0000ff;ffffff",  # Invalid hex char
            "2,2,hex:f0000;00ff00;0000ff;ffffff",  # Too short
            "2,2,hex:ff00000;00ff00;0000ff;ffffff",  # Too long
        ]
        for invalid in invalid_hex:
            with pytest.raises(encoder.EncodingError, match="Invalid hex"):
                encoder.decode_image(invalid)

    def test_decode_images_empty_list(self):
        """Test batch decoding with empty list."""
        with pytest.raises(ValueError, match="No encoded data provided"):
            encoder.decode_images([], "output")

    def test_decode_images_invalid_output_dir(self, encoded_rgb):
        """Test batch decoding with invalid output directory type."""
        with pytest.raises(TypeError, match="must be a string or Path"):
            encoder.decode_images([("test", encoded_rgb)], 123)

    def test_decode_images_mixed_success(self, temp_dir, encoded_rgb, encoded_hex):
        """Test batch decoding with mix of valid and invalid data."""
        encoded_data = [
            ("valid1.png", encoded_rgb),
            ("valid2.png", encoded_hex),
            ("invalid.png", "invalid:data"),
            ("invalid_type.png", 123),
        ]

        results = encoder.decode_images(encoded_data, temp_dir)

        assert len(results) == 4
        # First two should succeed
        assert isinstance(results[0][1], Path)
        assert isinstance(results[1][1], Path)
        # Last two should fail
        assert isinstance(results[2][1], encoder.EncodingError)
        assert isinstance(results[3][1], encoder.EncodingError)

    def test_decode_images_output_naming(self, temp_dir, encoded_rgb):
        """Test output filename handling in batch decode."""
        encoded_data = [
            ("test.jpg", encoded_rgb),  # Different extension
            ("path/to/test.png", encoded_rgb),  # With path
            (Path("test.png"), encoded_rgb),  # Path object
        ]

        results = encoder.decode_images(encoded_data, temp_dir)

        assert len(results) == 3
        assert all(isinstance(r[1], Path) for r in results)
        assert all(r[1].suffix == ".png" for r in results)
        assert all(r[1].parent == temp_dir for r in results)

    def test_successful_decode_roundtrip(self, temp_dir, sample_image):
        """Test full encode-decode roundtrip."""
        for format in ["rgb", "hex"]:
            # Encode
            encoded = encoder.encode_image(sample_image, format)

            # Decode
            decoded = encoder.decode_image(encoded)
            output_path = temp_dir / f"decoded_{format}.png"
            decoded.save(output_path)

            # Compare with original
            original = Image.open(sample_image)
            assert decoded.size == original.size
            assert decoded.mode == "RGB"

            # Check a few sample pixels
            for x in [0, decoded.width // 2, decoded.width - 1]:
                for y in [0, decoded.height // 2, decoded.height - 1]:
                    assert decoded.getpixel((x, y)) == original.convert("RGB").getpixel(
                        (x, y)
                    )

    def test_decode_rgb_format(self, temp_dir):
        """Test decoding from RGB format."""
        encoded = "2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255"
        img = encoder.decode_image(encoded)

        assert img.size == (2, 2)
        assert img.mode == "RGB"
        assert img.getpixel((0, 0)) == (255, 0, 0)
        assert img.getpixel((1, 0)) == (0, 255, 0)
        assert img.getpixel((0, 1)) == (0, 0, 255)
        assert img.getpixel((1, 1)) == (255, 255, 255)

    def test_decode_hex_format(self, temp_dir):
        """Test decoding from hex format."""
        encoded = "2,2,hex:ff0000;00ff00;0000ff;ffffff"
        img = encoder.decode_image(encoded)

        assert img.size == (2, 2)
        assert img.getpixel((0, 0)) == (255, 0, 0)
        assert img.getpixel((1, 0)) == (0, 255, 0)
        assert img.getpixel((0, 1)) == (0, 0, 255)
        assert img.getpixel((1, 1)) == (255, 255, 255)
