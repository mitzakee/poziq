# poziq

Transform images into puzzles.

A Python CLI tool for image manipulation. It provides functionality for slicing images into smaller pieces, encoding them in different formats, and reassembling them back together.

## Installation

```bash
pip install poziq
```

## Development

To set up the development environment:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Clone the repository
git clone https://github.com/mitzakee/poziq.git
cd poziq

# Install dependencies (choose one)
pip install -r requirements.txt                # Install from requirements.txt
pip install -e ".[dev]"                       # Install in editable mode with dev dependencies
```

Run tests:

```bash
pytest
```

Note: Always ensure your virtual environment is activated when working with the project. The command prompt should show `(venv)` when the environment is active.

## Usage

### Slicing Images

Split an image into smaller pieces using grid mode, dimension mode, or a mix of both:

```bash
# Grid mode: Split into 3x4 grid
poziq slice input.jpg output_dir/ --rows 3 --cols 4

# Dimension mode: Split into pieces of specific size
poziq slice input.jpg output_dir/ --slice-width 100 --slice-height 150

# Mixed mode: Fixed width with specific number of rows
poziq slice input.jpg output_dir/ --slice-width 100 --rows 3

# Mixed mode: Fixed height with specific number of columns
poziq slice input.jpg output_dir/ --slice-height 150 --cols 4
```

In mixed mode:

- `--slice-width` with `--rows`: Creates slices of fixed width, with height calculated to achieve the specified number of rows
- `--slice-height` with `--cols`: Creates slices of fixed height, with width calculated to achieve the specified number of columns

### Assembling Images

Combine sliced images back into the original:

```bash
poziq assemble slices/ output.jpg --rows 3 --cols 4
```

### Encoding Images

Convert images into text-based formats:

```bash
# RGB format (default)
poziq encode image.png encoded_dir/
# Creates: encoded_dir/image.pzq with content like:
# 2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255

# Hex format
poziq encode image.png encoded_dir/ -f hex
# Creates: encoded_dir/image.pzq with content like:
# 2,2,hex:ff0000;00ff00;0000ff;ffffff

# Encode multiple images
poziq encode image1.png image2.png encoded_dir/ -f hex
```

### Decoding Images

Convert encoded text back into images:

```bash
# Decode single file
poziq decode encoded.pzq decoded_dir/

# Decode multiple files
poziq decode file1.pzq file2.pzq decoded_dir/
```

## File Formats

### PZQ Format

The `.pzq` format is a simple text-based format for representing images. The format consists of two parts separated by a colon (`:`):

1. Header: `width,height,colorformat`

   - Image dimensions (e.g., `2,3`)
   - Color format: Either `rgb` or `hex`

2. Data: Semicolon-separated pixel values
   - RGB format: `r,g,b` values (0-255)
   - Hex format: 6-character hex color code without `#` prefix

Examples:

```
# RGB format (2x2 image)
2,2,rgb:255,0,0;0,255,0;0,0,255;255,255,255

# Hex format (2x2 image)
2,2,hex:ff0000;00ff00;0000ff;ffffff
```

The pixels are stored row by row, from left to right, top to bottom.

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool was created as a Christmas present to make learning CS concepts more engaging through hands-on challenges. It's a personal project with a very specific purpose, and while it works well for its intended use, I'm not planning to actively maintain or extend it beyond its current scope.

Feel free to:

- Use it as inspiration for your own learning projects
- Fork it and adapt it to your needs
- Submit issues if you find any bugs

But please note:

- Feature requests will likely not be implemented
- The tool is provided as-is
- Support will be minimal
