from pathlib import Path

import click

from . import image


@click.group()
def cli():
    """poziq - A tool for slicing, encoding, and assembling images."""
    pass


@cli.command()
@click.argument('image_path', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--slice-size', '-s', type=int, default=100, help='Size of each slice in pixels')
def slice(image_path: Path, output_dir: Path, slice_size: int):
    """Slice an image into smaller pieces."""
    try:
        # Slice the image
        slices = image.slice_image(image_path, slice_size)

        # Save the slices
        # saved_paths = image.save_slices(slices, output_dir)

        # Report success
        # click.echo(f"Successfully sliced image into {len(saved_paths)} pieces")
        # click.echo(f"Slices saved in: {output_dir}")

    except (ValueError, TypeError) as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except FileNotFoundError:
        click.echo(f"Error: Image file not found: {image_path}", err=True)
        raise click.Abort()
    except OSError as e:
        click.echo(f"Error: Failed to process image: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
