import pytest
from PIL import Image

from poziq import cli
from .fixtures import sample_image, sample_slices, temp_dir, runner


class TestSliceCliCommand:
    """Test suite for slice command CLI interface."""

    def test_slice_grid_mode_cli(self, temp_dir, sample_image, runner):
        """Test CLI slicing with grid parameters."""
        output_dir = temp_dir / "slices"
        result = runner.invoke(
            cli.cli,
            ["slice", str(sample_image), str(output_dir), "--rows", "2", "--cols", "3"],
        )

        assert result.exit_code == 0
        assert "Successfully sliced" in result.output
        assert len(list(output_dir.glob("*.png"))) == 6

    def test_slice_dimensions_mode_cli(self, temp_dir, sample_image, runner):
        """Test CLI slicing with dimension parameters."""
        output_dir = temp_dir / "slices"
        result = runner.invoke(
            cli.cli,
            [
                "slice",
                str(sample_image),
                str(output_dir),
                "--slice-width",
                "100",
                "--slice-height",
                "150",
            ],
        )

        assert result.exit_code == 0
        assert "Successfully sliced" in result.output
        assert all(Image.open(p).size == (100, 150) for p in output_dir.glob("*.png"))

    def test_slice_missing_parameters(self, temp_dir, sample_image, runner):
        """Test CLI error handling with missing parameters."""
        output_dir = temp_dir / "slices"
        result = runner.invoke(cli.cli, ["slice", str(sample_image), str(output_dir)])

        assert result.exit_code != 0
        assert "Must specify either" in result.output

    def test_slice_custom_prefix_extension(self, temp_dir, sample_image, runner):
        """Test CLI with custom prefix and extension."""
        output_dir = temp_dir / "slices"
        result = runner.invoke(
            cli.cli,
            [
                "slice",
                str(sample_image),
                str(output_dir),
                "--rows",
                "2",
                "--cols",
                "2",
                "--prefix",
                "custom",
                "--extension",
                "webp",
            ],
        )

        assert result.exit_code == 0
        assert len(list(output_dir.glob("custom_*.webp"))) == 4


class TestAssembleCliCommand:
    """Test suite for assemble command CLI interface."""

    def test_cli_success(self, temp_dir, sample_slices, runner):
        """Test successful CLI execution."""
        output_path = temp_dir / "assembled.png"
        result = runner.invoke(
            cli.cli,
            ["assemble", str(temp_dir), str(output_path), "--rows", "2", "--cols", "2"],
        )
        assert result.exit_code == 0
        assert output_path.exists()
        assert Image.open(output_path).size == (200, 300)

    def test_cli_invalid_rows_cols(self, temp_dir, sample_slices, runner):
        """Test CLI with invalid row/column count."""
        output_path = temp_dir / "assembled.png"
        result = runner.invoke(
            cli.cli,
            ["assemble", str(temp_dir), str(output_path), "--rows", "3", "--cols", "2"],
        )
        assert result.exit_code != 0
        assert "Expected" in result.output
        assert not output_path.exists()


class TestEncodeCliCommand:
    """Test suite for encode command CLI interface."""

    def test_encode_cli_rgb(self, temp_dir, sample_image, runner):
        """Test CLI encoding with RGB format."""
        output_dir = temp_dir / "encoded"
        result = runner.invoke(
            cli.cli,
            ["encode", str(sample_image), str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Successfully encoded" in result.output

        encoded_files = list(output_dir.glob("*.pzq"))
        assert len(encoded_files) == 1

        # Verify content format
        content = encoded_files[0].read_text()
        assert content.startswith("400,300,rgb:")

    def test_encode_cli_hex(self, temp_dir, sample_image, runner):
        """Test CLI encoding with hex format."""
        output_dir = temp_dir / "encoded"
        result = runner.invoke(
            cli.cli,
            ["encode", str(sample_image), str(output_dir), "-f", "hex"],
        )

        assert result.exit_code == 0
        encoded_files = list(output_dir.glob("*.pzq"))
        content = encoded_files[0].read_text()
        assert content.startswith("400,300,hex:")

    def test_encode_multiple_files(self, temp_dir, sample_image, runner):
        """Test encoding multiple files."""
        # Create a second test image
        img2_path = temp_dir / "test2.png"
        Image.new("RGB", (100, 100), color="blue").save(img2_path)

        # Encode both images
        encoded_dir = temp_dir / "encoded"
        result = runner.invoke(
            cli.cli,
            ["encode", str(sample_image), str(img2_path), str(encoded_dir)],
        )

        assert result.exit_code == 0
        encoded_files = list(encoded_dir.glob("*.pzq"))
        assert len(encoded_files) == 2
        assert all(f.suffix == ".pzq" for f in encoded_files)

    def test_encode_invalid_format(self, temp_dir, sample_image, runner):
        """Test encoding with invalid format option."""
        output_dir = temp_dir / "encoded"
        result = runner.invoke(
            cli.cli,
            ["encode", str(sample_image), str(output_dir), "-f", "invalid"],
        )

        assert result.exit_code != 0


class TestDecodeCliCommand:
    """Test suite for decode command CLI interface."""

    def test_decode_cli_success(self, temp_dir, runner):
        """Test successful CLI decoding."""
        # Create an encoded file
        encoded_dir = temp_dir / "encoded"
        encoded_dir.mkdir()
        encoded_file = encoded_dir / "test.pzq"
        encoded_file.write_text("2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255")

        # Decode it
        output_dir = temp_dir / "decoded"
        result = runner.invoke(
            cli.cli,
            ["decode", str(encoded_file), str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Successfully decoded" in result.output

        decoded_files = list(output_dir.glob("*.png"))
        assert len(decoded_files) == 1

        # Verify decoded image
        img = Image.open(decoded_files[0])
        assert img.size == (2, 2)
        assert img.getpixel((0, 0)) == (255, 0, 0)

    def test_decode_multiple_files(self, temp_dir, runner):
        """Test decoding multiple files."""
        # Create encoded files
        encoded_dir = temp_dir / "encoded"
        encoded_dir.mkdir()

        # Create two encoded files
        encodings = [
            ("test1.pzq", "2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255"),
            ("test2.pzq", "2,1,hex:ff0000;00ff00"),
        ]
        encoded_files = []
        for name, content in encodings:
            path = encoded_dir / name
            path.write_text(content)
            encoded_files.append(path)

        # Decode all files
        decoded_dir = temp_dir / "decoded"
        result = runner.invoke(
            cli.cli,
            ["decode"] + [str(p) for p in encoded_files] + [str(decoded_dir)],
        )

        assert result.exit_code == 0
        assert len(list(decoded_dir.glob("*.png"))) == 2

    def test_decode_invalid_extension(self, temp_dir, runner):
        """Test decoding with invalid file extension."""
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255")

        output_dir = temp_dir / "decoded"
        result = runner.invoke(
            cli.cli,
            ["decode", str(invalid_file), str(output_dir)],
        )

        assert result.exit_code != 0
        assert "must have .pzq extension" in result.output

    def test_decode_invalid_content(self, temp_dir, runner):
        """Test decoding with invalid file content."""
        invalid_file = temp_dir / "invalid.pzq"
        invalid_file.write_text("invalid content")

        output_dir = temp_dir / "decoded"
        result = runner.invoke(
            cli.cli,
            ["decode", str(invalid_file), str(output_dir)],
        )

        assert result.exit_code != 0
        assert "Error:" in result.output

    def test_decode_nonexistent_file(self, temp_dir, runner):
        """Test decoding with nonexistent input file."""
        output_dir = temp_dir / "decoded"
        result = runner.invoke(
            cli.cli,
            ["decode", str(temp_dir / "nonexistent.pzq"), str(output_dir)],
        )

        assert result.exit_code != 0
        assert "Error:" in result.output
