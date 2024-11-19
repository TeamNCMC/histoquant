"""
create_pyramids command line interface (CLI).
You can set up your settings filling the variables at the top of the file and run the
script :
> python create_pyramids.py /path/to/your/images

Or alternatively, you can run the script as a CLI :
> python create_pyramids.py [options] /path/to/your/images

Example :
> python create_pyramids.py --tile-size 1024 --pyramid-factor 4 /path/to/your/images

To get help (eg. list all options), run :
> python create_pyramids.py --help

To use the QuPath backend, you'll need the companion 'createPyramids.groovy' script.

author : Guillaume Le Goc (g.legoc@posteo.org) @ NeuroPSI
version : 2024.11.19

"""

import math
import multiprocessing
import os
import subprocess
import sys
import uuid
import warnings
from typing import Optional

import typer
from tqdm import tqdm
from typing_extensions import Annotated

__version__ = 1.2

# --- Parameters (default values)
TILE_SIZE: int = 512
"""Tile size (usually 512 or 1024)."""
PYRAMID_FACTOR: int = 2
"""Factor between two consecutive pyramid levels."""
NTHREADS: int = int(multiprocessing.cpu_count() / 2)
"""Number of threads for parallelization."""

# --- QuPath backend parameters (default values)
USE_QUPATH: bool = True
"""Use QuPath and the external groovy script instead of pure python (more reliable)."""
SCRIPT_PATH: str = os.path.join(os.path.dirname(__file__), "createPyramids.groovy")
"""Full path to the groovy script that does the job."""
QUPATH_PATH: str = (
    "C:/Users/glegoc/AppData/Local/QuPath-0.5.1/QuPath-0.5.1 (console).exe"
)
"""Full path to the QuPath (console) executable."""
PYRAMID_MAX: int = 32
"""Maximum rescaling (smaller pyramid)."""

INEXT: str = "ome.tiff"
"""Input files extension."""
COMPRESSION_PYTHON: str = "LZW"
"""Compression method."""


# --- Typer functions
def version_callback(value: bool):
    if value:
        print(f"create-pyramids CLI version : {__version__}")
        raise typer.Exit()


# --- Processing functions
def pyramidalize_qupath(
    image_path: str,
    output_image: str,
    qupath_path: str,
    script_path: str,
    tile_size: int,
    pyramid_factor: int,
    nthreads: int,
):
    """
    Pyramidalization with QuPath backend.

    """
    # generate an uid to make sure to not overwrite original file
    uid = uuid.uuid1().hex

    # prepare image names
    imagename = os.path.basename(image_path)
    inputdir = os.path.dirname(image_path)
    new_imagename = uid + "_" + imagename
    new_imagepath = os.path.join(inputdir, new_imagename)

    # prepare arguments
    args = "[" f"{uid}," f"{tile_size}," f"{pyramid_factor}," f"{nthreads}" "]"

    # call the qupath groovy script within a shell
    subprocess.run(
        [qupath_path, "script", script_path, "-i", image_path, "--args", args],
        shell=True,
        stdout=subprocess.DEVNULL,
    )

    if not os.path.isfile(new_imagepath):
        raise FileNotFoundError(
            "QuPath did not manage to create the pyramidalized image."
        )

    # move the pyramidalized image in the output directory
    os.rename(new_imagepath, output_image)


def pyramidalize_python(
    image_path: str, output_image: str, levels: list | tuple, tiffoptions: dict
):
    """
    Pyramidalization with tifffile and scikit-image.

    Parameters
    ----------
    image_path : str
        Full path to the image.
    output_image : str
        Full path to the pyramidalized image.
    levels : list-like of int
        Pyramids levels.
    tiffoptions : dict
        Options for TiffWriter.
    """
    # specific imports
    import xml.etree.ElementTree as ET

    import numpy as np
    import tifffile
    from skimage import transform

    # Nested functions
    def get_pixelsize_ome(
        desc: str,
        namespace: dict = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"},
    ) -> float:
        """
        Extract physical pixel size from OME-XML description.

        Raise a warning if pixels are anisotropic (eg. X and Y sizes are not the same).
        Raise an error if size units are not microns ("µm").

        Parameters
        ----------
        desc : str
            OME-XML string from Tiff page.
        namespace : dict, optional
            XML namespace, defaults to latest OME-XML schema (2016-06).

        Returns
        -------
        pixelsize : float
            Physical pixel size.

        """
        root = ET.fromstring(desc)

        for pixels in root.findall(".//ome:Pixels", namespace):
            pixelsize_x = float(pixels.get("PhysicalSizeX"))
            pixelsize_y = float(pixels.get("PhysicalSizeY"))
            break  # stop at first Pixels field in the XML

        # sanity checks
        if pixelsize_x != pixelsize_y:
            warnings.warn(
                f"Anisotropic pixels size found, are you sure ? ({pixelsize_x}, {pixelsize_y})"
            )

        return np.mean([pixelsize_x, pixelsize_y])

    def im_downscale(img, downfactor, **kwargs):
        """
        Downscale an image by the given factor.

        Wrapper for `skimage.transform.rescale`.

        Parameters
        ----------
        img : np.ndarray
        downfactor : int or float
            Downscaling factor.
        **kwargs : passed to skimage.transform.rescale

        Returns
        -------
        img_rs : np.ndarray
            Rescaled image.

        """
        return transform.rescale(
            img, 1 / downfactor, anti_aliasing=False, preserve_range=True, **kwargs
        )

    # get metadata from original file (without loading the whole image)
    with tifffile.TiffFile(image_path) as tifin:
        metadata = tifin.ome_metadata
        pixelsize = get_pixelsize_ome(metadata)

    with tifffile.TiffWriter(output_image, ome=False) as tifout:
        # read full image
        img = tifffile.imread(image_path)

        # write full resolution multichannel image
        tifout.write(
            img,
            subifds=len(levels),
            resolution=(1e4 / pixelsize, 1e4 / pixelsize),
            description=metadata,
            metadata=None,
            **tiffoptions,
        )

        # write downsampled images (pyramidal levels)
        for level in levels:
            img_down = im_downscale(
                img, level, order=0, channel_axis=0
            )  # downsample image
            tifout.write(
                img_down,
                subfiletype=1,
                resolution=(1e4 / level / pixelsize, 1e4 / level / pixelsize),
                **tiffoptions,
            )


def get_tiff_options(compression: str, nthreads: int, tilesize: int) -> dict:
    """
    Get the relevant tags and options to write a TIFF file.

    The returned dict is meant to be used to write a new tiff page with those tags.

    Parameters
    ----------
    compression : str
        Tiff compression (None, LZW, ...).
    nthreads : int
        Number of threads to write tiles.
    tilesize : int
        Tile size in pixels. Should be a power of 2.

    Returns
    -------
    options : dict
        Dictionary with Tiff tags.

    """
    return {
        "compression": compression,
        "photometric": "minisblack",
        "resolutionunit": "CENTIMETER",
        "maxworkers": nthreads,
        "tile": (tilesize, tilesize),
    }


def pyramidalize_directory(
    inputdir: Annotated[
        str,
        typer.Argument(help="Full path to the directory with images to pyramidalize."),
    ],
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True),
    ] = None,
    use_qupath: Annotated[
        Optional[bool],
        typer.Option(help="Use QuPath backend instead of Python."),
    ] = USE_QUPATH,
    tile_size: Annotated[
        Optional[int],
        typer.Option(help="Image tile size, typically 512 or 1024."),
    ] = TILE_SIZE,
    pyramid_factor: Annotated[
        Optional[int],
        typer.Option(help="Factor between two consecutive pyramid levels."),
    ] = PYRAMID_FACTOR,
    nthreads: Annotated[
        Optional[int],
        typer.Option(help="Number of threads to parallelize image writing."),
    ] = NTHREADS,
    qupath_path: Annotated[
        Optional[str],
        typer.Option(
            help="Full path to the QuPath (console) executable.",
            rich_help_panel="QuPath backend",
        ),
    ] = QUPATH_PATH,
    script_path: Annotated[
        Optional[str],
        typer.Option(
            help="Full path to the groovy script that does the job.",
            rich_help_panel="QuPath backend",
        ),
    ] = SCRIPT_PATH,
    pyramid_max: Annotated[
        Optional[int],
        typer.Option(
            help="Maximum rescaling (smaller pyramid, will be rounded to closer power of 2).",
            rich_help_panel="Python backend",
        ),
    ] = PYRAMID_MAX,
):
    """
    Create pyramidal versions of .ome.tiff images found in the input directory.
    You need to edit the script to set the "QUPATH_PATH" to your installation of QuPath.
    Usually on Windows it should be here :
    C:/Users/$USERNAME$/AppData/Local/QuPath-0.X.Y/QuPath-0.X.Y (console).exe
    Alternatively you can run the script with the --qupath-path option.

    """
    # check QuPath was correctly set
    if not os.path.isfile(qupath_path):
        raise FileNotFoundError(
            """QuPath executable was not found. Edit the script to set 'QUPATH_PATH',
            or run the script with the --qupath-path  option. Usually it is installed
            at C:/Users/$USERNAME$/AppData/Local/QuPath-0.X.Y/QuPath-0.X.Y (console).exe"""
        )
    # prepare output directory
    outputdir = os.path.join(inputdir, "pyramidal")
    if not os.path.isdir(outputdir):
        os.mkdir(outputdir)

    # get a list of images
    files = [filename for filename in os.listdir(inputdir) if filename.endswith(INEXT)]

    # check we have files to process
    if len(files) == 0:
        print("Specified input directory is empty.")
        sys.exit()

    # loop over all files
    print(f"Found {len(files)} to pyramidalize...")

    pbar = tqdm(files)
    for imagename in pbar:
        # prepare image names
        image_path = os.path.join(inputdir, imagename)
        output_image = os.path.join(outputdir, imagename)

        # check if output file already exists
        if os.path.isfile(output_image):
            continue

        # verbose
        pbar.set_description(f"Pyramidalyzing {imagename}")

        if use_qupath:
            pyramidalize_qupath(
                image_path,
                output_image,
                qupath_path,
                script_path,
                tile_size,
                pyramid_factor,
                nthreads,
            )
        else:
            # prepare tiffwriter options
            tiffoptions = get_tiff_options(COMPRESSION_PYTHON, nthreads, tile_size)

            # number of pyramid levels
            levels = [
                pyramid_factor**i
                for i in range(1, int(math.log(pyramid_max, pyramid_factor)) + 1)
            ]
            pyramidalize_python(image_path, output_image, levels, tiffoptions)

    print("All done!")


# --- Call
if __name__ == "__main__":
    typer.run(pyramidalize_directory)
