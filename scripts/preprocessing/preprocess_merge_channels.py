"""
Script for preprocessing.
Merge channels found in wdir/Stack_RIP/ch*_cleaned, and create pyramidal OME-TIFF.
Specify options at the top of file.
`CHANNELS` must be ordered as the channels in the Stack_RIP directory.

Double check channel names and colors.

Credits to Christoph Gohlke, see
https://forum.image.sc/t/creating-a-multi-channel-pyramid-ome-tiff-with-tiffwriter-in-python/76424/4

author : Guillaume Le Goc (g.legoc@posteo.org)
version : 2024.11.19

"""

import os
import sys
import warnings

import numpy as np
import tifffile
from skimage import transform
from tqdm import tqdm

# --- Parameters
EXPID = "animal0"

# channels settings : dict mapping channel name to an RGB color. The order must be the
# same as the channels order in the Stack_RIP directory.
CHANNELS = {
    "CFP": (0, 0, 255),
    "EGFP": (0, 255, 0),
}

# pyramidal ome-tiff settings
LEVELS = (2, 4, 16, 32)  # downsampling factors for pyramid levels
COMPRESSION = "LZW"  # compression, None or LZW
TILESIZE = 512  # tiles size
NTHREADS = 18  # number of threads for writing image

IN_EXT = "tiff"

# working directory
WDIR = "path/to/data"


def rgb_to_int(rgb):
    """Convert RGB color tuple to integer for OME-TIFF specs.
    Alpha channel is set to 0.

    Parameters
    ----------
    rgb: tuple or list

    Returns
    -------
    intcol : int

    """
    return int.from_bytes([rgb[0], rgb[1], rgb[2], 0], byteorder="big", signed=True)


def get_ome_metadata(pixelsize, chan_names, chan_colors):
    """
    Return a dictionnary that provides OME-TIFF metadata.

    chan_names and chan_colors must have the same order.


    Parameters
    ----------
    pixelsize : float
        Pixel size in microns.
    chan_names : tuple or list of str
        Names of channels in the order they are stored in. eg ("CFP", "EGFP")
    chan_colors : tuple or list of tuple of int
        List of RGB triplets, 255-based. eg ((0, 0, 255), (0, 255, 0)).

    Returns
    -------
    metadata : dict
        OME-TIFF compatible dict to use in tifffile.TiffWriter.write.

    """
    return {
        "axes": "CYX",
        "Name": None,
        "DimensionOrder": "XYCZT",
        "PhysicalSizeX": pixelsize,
        "PhysicalSizeXUnit": "µm",
        "PhysicalSizeY": pixelsize,
        "PhysicalSizeYUnit": "µm",
        "Channel": {
            "Name": list(chan_names),
            "Color": [rgb_to_int(color) for color in chan_colors],
        },
        "SizeC": len(chan_names),
        "SizeT": 1,
        "SizeZ": 1,
    }


def get_tiff_options(compression=COMPRESSION, nthreads=NTHREADS, tilesize=TILESIZE):
    """
    Get the relevant tags and options to write a TIFF file.

    The returned dict is meant to be used to write a new tiff page with those tags.

    Parameters
    ----------
    compression : str, optional
        Tiff compression (None, LZW, ...). Default is COMPRESSION global variable.
    nthreads : int, optional
        Number of threads to write tiles. Default is NTHREADS global variable.
    tilesize : int, optional
        Tile size in pixels. Should be a power of 2. Default is TILESIZE global variable.

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


def get_pixelsize_ij(tif):
    """
    Get physical pixel size from a Tiff written as ImageJ tiff file.

    The input TiffFile must be a single-page Tiff.

    Parameters
    ----------
    tif : tifffile.TiffFile
        TiffFile object.

    Returns
    -------
    pixelsize : float
        Pixel size in microns.

    """
    xsize, xunit = tif.pages[0].tags["XResolution"].value
    ysize, yunit = tif.pages[0].tags["YResolution"].value

    pixelsize_x = xunit / xsize
    pixelsize_y = yunit / ysize

    # sanity check
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


def process_directory(
    expid: str,
    levels: tuple,
    channels: dict,
):
    """
    Merge TIFF stacks representing different channels and create pyramidal OME-TIFF.

    wdir/expid/images is scanned for directories chXX_cleaned, images are collected and merged.

    Parameters
    ----------
    expid : str
        Experiment ID.
    levels : tuple
        Pyramid levels.
    channels : dict
        Mapping channels names to channels colors.

    """
    # --- Preparation
    wdir = os.path.abspath(WDIR)

    # build directories names
    inpdir = os.path.join(wdir, expid, "images")
    outdir = os.path.join(wdir, expid, "images", "merged_cleaned_pyramid")

    # create directory if it does not exist
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    # list channel directories
    chandirslist = [
        os.path.join(inpdir, directory)
        for directory in os.listdir(inpdir)
        if (
            os.path.isdir(os.path.join(wdir, expid, "images", directory))
            and directory.startswith("ch")
            and directory.endswith("cleaned")
        )
    ]
    nchannels = len(chandirslist)  # number of channels

    # sanity checks
    if nchannels == 0:
        print("[Error] No channels found in the input directory.")
        sys.exit()
    elif nchannels != len(channels):
        raise ValueError(
            f"Found {nchannels}, but only {len(channels)} provided in CHANNELS : {channels}"
        )

    # get list of images for first channel
    imgslist = [file for file in os.listdir(chandirslist[0]) if file.endswith(IN_EXT)]

    # prepare TiffWriter options
    options = get_tiff_options(
        compression=COMPRESSION, nthreads=NTHREADS, tilesize=TILESIZE
    )

    # number of pyramid levels
    nlevels = len(levels)

    # --- Processing

    # loop through all images
    pbar = tqdm(imgslist)
    for imgfile in pbar:
        # build output image name
        imgout = os.path.join(outdir, os.path.splitext(imgfile)[0] + ".ome.tiff")

        if os.path.isfile(imgout):
            continue

        pbar.set_description(f"Merging and pyramidizing {imgfile}")

        # get image information (without loading)
        with tifffile.TiffFile(os.path.join(chandirslist[0], imgfile)) as tif:
            shape = (nchannels,) + tif.pages[0].shape  # (CYX)
            dtype = tif.pages[0].dtype
            pixelsize = get_pixelsize_ij(tif)

        # prepare OME-TIFF metadata
        metadata = get_ome_metadata(pixelsize, channels.keys(), channels.values())

        with tifffile.TiffWriter(imgout, ome=True) as tifout:
            img = np.empty(shape, dtype=dtype)  # initialize empty 3D array CYX
            for channelid in range(nchannels):  # loop through channels
                # build input image name
                imgname = os.path.join(chandirslist[channelid], imgfile)

                # read images
                img[channelid, :] = tifffile.imread(imgname)

            # write full resolution multichannel image
            tifout.write(
                img,
                subifds=nlevels,
                resolution=(1e4 / pixelsize, 1e4 / pixelsize),
                metadata=metadata,
                **options,
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
                    **options,
                )

        pbar.set_description("Done")


# --- Call
if __name__ == "__main__":
    process_directory(
        EXPID,
        LEVELS,
        CHANNELS,
    )
