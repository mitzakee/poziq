import pytest
from PIL import Image

from poziq import cli
from .fixtures import sample_image, sample_slices, temp_dir


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


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    from click.testing import CliRunner

    return CliRunner()
