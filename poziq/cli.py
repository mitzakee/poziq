from pathlib import Path

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
@click.option('--slice-size', '-s', type=int, default=100, help='Size of each slice in pixels')
# fmt: on
def slice(image_path: Path, output_dir: Path, slice_size: int):
    """Slice an image into smaller pieces."""
    try:
        # Slice the image
        slices = image.slice_image(image_path, slice_size)

        # Save the slices
        saved_paths = image.save_slices(slices, output_dir)

        # Report success
        click.echo(f"Successfully sliced image into {len(saved_paths)} pieces")
        click.echo(f"Slices saved in: {output_dir}")

    except (ValueError, TypeError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo(f"Error: Image file not found: {image_path}", err=True)
        raise click.Abort()
    except OSError as e:
        click.echo(f"Error: Failed to process image: {str(e)}", err=True)
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
        assembled = image.assemble_image(
            slice_dir, rows, cols, prefix, extension
        )

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
