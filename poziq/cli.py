from pathlib import Path
from typing import Union

import click

from . import image


@click.group()
def cli():
    """poziq - A tool for slicing, encoding, and assembling images."""
    pass


# fmt: off
@cli.command()
@click.argument('image_path', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--rows', '-r', type=int, help='Number of rows to slice into')
@click.option('--cols', '-c', type=int, help='Number of columns to slice into')
@click.option('--slice-width', '-w', type=int, help='Width of each slice in pixels (takes priority over cols)')
@click.option('--slice-height', '-h', type=int, help='Height of each slice in pixels (takes priority over rows)')
@click.option('--prefix', '-p', type=str, default="slice", help='Prefix for output filenames')
@click.option('--extension', '-e', type=str, default="png",
              help=f'Output image format (supported: {", ".join(sorted(image.SUPPORTED_EXTENSIONS))})')
# fmt: on
def slice(
    image_path: Path,
    output_dir: Path,
    rows: Union[int, None],
    cols: Union[int, None],
    slice_width: Union[int, None],
    slice_height: Union[int, None],
    prefix: str,
    extension: str,
):
    """
    Slice an image into a grid of smaller pieces.

    Can be specified either by grid size (--rows and --cols) or slice dimensions
    (--slice-width and --slice-height). If both are provided, slice dimensions take priority.
    """
    try:
        # Validate that at least one set of dimensions is provided
        using_dimensions = slice_width is not None or slice_height is not None
        using_grid = rows is not None and cols is not None

        if not (using_dimensions or using_grid):
            raise click.UsageError(
                "Must specify either (--rows and --cols) or (--slice-width and/or --slice-height)"
            )

        # Validate output extension
        extension = image.validate_extension(extension)

        # Slice the image
        slices = image.slice_image(
            image_path,
            rows=rows,
            cols=cols,
            slice_width=slice_width,
            slice_height=slice_height,
        )

        # Save the slices
        saved_paths = image.save_slices(slices, output_dir, prefix, extension)

        # Report success with appropriate dimensionality
        if using_dimensions:
            dimensions = (
                f"{slice_width}x{slice_height}"
                if slice_width and slice_height
                else "custom"
            )
            click.echo(
                f"Successfully sliced image into {len(saved_paths)} pieces (slice size: {dimensions})"
            )
        else:
            click.echo(
                f"Successfully sliced image into {len(saved_paths)} pieces ({rows}x{cols} grid)"
            )
        click.echo(f"Slices saved in: {output_dir}")

    except (ValueError, TypeError, AssertionError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except click.UsageError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo(f"Error: Image file not found: {image_path}", err=True)
        raise click.Abort()
    except OSError as e:
        click.echo(f"Error: Failed to process image: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()


# fmt: off
@cli.command()
@click.argument('slice_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument('output_path', type=click.Path(path_type=Path))
@click.option('--rows', '-r', type=int, required=True, help='Number of rows in the original image grid')
@click.option('--cols', '-c', type=int, required=True, help='Number of columns in the original image grid')
@click.option('--prefix', '-p', type=str, default="slice", help='Prefix used in slice filenames')
@click.option('--extension', '-e', type=str, default="png",
              help=f'File extension for slice images (supported: {", ".join(sorted(image.SUPPORTED_EXTENSIONS))})')
# fmt: on
def assemble(
    slice_dir: Path,
    output_path: Path,
    rows: int,
    cols: int,
    prefix: str,
    extension: str,
):
    """Assemble slices back into a complete image."""
    try:
        # Validate output path extension
        output_ext = output_path.suffix.lstrip(".").lower()
        if output_ext not in image.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported output format: {output_ext}\n"
                f"Supported formats: {', '.join(sorted(image.SUPPORTED_EXTENSIONS))}"
            )

        # Assemble the image
        assembled = image.assemble_image(slice_dir, rows, cols, prefix, extension)

        # Save the result
        assembled.save(output_path)

        click.echo(f"Successfully assembled image saved to: {output_path}")

    except (ValueError, TypeError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except (FileNotFoundError, NotADirectoryError):
        click.echo(f"Error: Directory not found: {slice_dir}", err=True)
        raise click.Abort()
    except OSError as e:
        click.echo(f"Error: Failed to process images: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
