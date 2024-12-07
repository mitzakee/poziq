import pytest
from PIL import Image

from poziq import cli

from .test_image import sample_slices, temp_dir


class TestCLI:
    """Test suite for CLI functionality."""

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
