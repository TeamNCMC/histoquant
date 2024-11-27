"""
Script to segment objects from images.

For fiber-like objects, binarize and skeletonize the image, then use `skan` to extract
branches coordinates.
For polygon-like objects, binarize the image and detect objects and extract contours
coordinates.
For points, treat that as polygons then extract the centroids instead of contours.
Finally, export the coordinates as collections in geojson files, importable in QuPath.
Supports any number of channel of interest within the same image. One file output file
per channel will be created.

This script uses `histoquant.seg`. It is designed to work on probability maps generated
from a pixel classifier in QuPath, but *might* work on raw images.

Usage : fill-in the Parameters section of the script and run it.
A "geojson" folder will be created in the parent directory of `IMAGES_DIR`.
To exclude objects near the edges of an ROI, specify the path to masks stored as images
with the same names as probabilities images (without their suffix).

Author : Guillaume Le Goc (g.legoc@posteo.org) @ NeuroPSI
Version : 2024.11.27

"""

import os
from datetime import datetime
from pathlib import Path

import geojson
import pandas as pd
import tifffile
from tqdm import tqdm

import histoquant as hq

pd.options.mode.copy_on_write = True  # prepare for pandas 3

# --- Parameters
IMAGES_DIR = "/path/to/images/to/segment"
"""Full path to the images to segment."""
MASKS_DIR = "path/to/corresponding/masks"
"""Full path to the masks, to exclude objects near the brain edges (set to None or empty
string to disable this feature)."""
MASKS_EXT = "tiff"
"""Masks files extension."""
SEGTYPE = "fibers"
"""Type of segmentation."""
IMG_SUFFIX = "_Probabilities.tiff"
"""Images suffix, including extension. Masks must be the same name without the suffix."""

CHANNELS_PARAMS = [
    {
        "name": "cy5",
        "target_channel": 0,
        "proba_threshold": 0.85,
        "qp_class": "Fibers: Cy5",
        "qp_color": [164, 250, 120],
    },
    {
        "name": "dsred",
        "target_channel": 1,
        "proba_threshold": 0.85,
        "qp_class": "Fibers: DsRed",
        "qp_color": [224, 153, 18],
    },
    {
        "name": "egfp",
        "target_channel": 2,
        "proba_threshold": 0.85,
        "qp_class": "Fibers: EGFP",
        "qp_color": [135, 11, 191],
    },
]
"""This should be a list of dictionary (one per channel) with keys :

- name: str, used as suffix for output geojson files, not used if only one channel
- target_channel: int, index of the segmented channel of the image, 0-based
- proba_threshold: float < 1, probability cut-off for that channel
- qp_class: str, name of QuPath classification
- qp_color: list of RGB values, associated color"""

EDGE_DIST = 50
"""Distance to brain edge to ignore, in µm. 0 to disable."""

FILTERS = {
    "length_low": 1.5,  # minimal length in microns - for lines
    "area_low": 1.1,  # minimal area in µm² - for polygons and points
    "area_high": 10,  # maximal area in µm² - for polygons and points
    "ecc_low": 0.0,  # minimal eccentricity - for polygons  and points (0 = circle)
    "ecc_high": 0.9,  # maximal eccentricity - for polygons and points (1 = line)
    "dist_thresh": 30,  # maximal inter-point distance in µm - for points
}
"""Dictionary with keys :

- length_low: minimal length in microns - for lines
- area_low: minimal area in µm² - for polygons and points
- area_high: maximal area in µm² - for polygons and points
- ecc_low: minimal eccentricity - for polygons  and points (0 = circle)
- ecc_high: maximal eccentricity - for polygons and points (1 = line)
- dist_thresh: maximal inter-point distance in µm - for points
"""

QUPATH_TYPE = "detection"
""" QuPath object type."""
MAX_PIX_VALUE = 255
"""Maximum pixel possible value to adjust `proba_threshold`."""

# --- Functions


def get_seg_method(segtype: str):
    """
    Determine what kind of segmentation is performed.

    Segmentation kind are, for now, lines, polygons or points. We detect that based on
    hardcoded keywords.

    Parameters
    ----------
    segtype : str

    Returns
    -------
    seg_method : str

    """

    line_list = ["fibers", "axons", "fiber", "axon"]
    point_list = ["synapto", "synaptophysin", "syngfp", "boutons", "points"]
    polygon_list = ["cells", "polygon", "polygons", "polygon", "cell"]

    if segtype in line_list:
        seg_method = "lines"
    elif segtype in polygon_list:
        seg_method = "polygons"
    elif segtype in point_list:
        seg_method = "points"
    else:
        raise ValueError(
            f"Could not determine method to use based on segtype : {segtype}."
        )

    return seg_method


def get_geojson_dir(images_dir: str):
    """
    Get the directory of geojson files, which will be in the parent directory
    of `images_dir`.

    If the directory does not exist, create it.

    Parameters
    ----------
    images_dir : str

    Returns
    -------
    geojson_dir : str

    """

    geojson_dir = os.path.join(Path(images_dir).parent, "geojson")

    if not os.path.isdir(geojson_dir):
        os.mkdir(geojson_dir)

    return geojson_dir


def get_geojson_properties(name: str, color: tuple | list, objtype: str = "detection"):
    """
    Return geojson objects properties as a dictionnary, ready to be used in geojson.Feature.

    Parameters
    ----------
    name : str
        Classification name.
    color : tuple or list
        Classification color in RGB (3-elements vector).
    objtype : str, optional
        Object type ("detection" or "annotation"). Default is "detection".

    Returns
    -------
    props : dict

    """

    return {
        "objectType": objtype,
        "classification": {"name": name, "color": color},
        "isLocked": "true",
    }


def parameters_as_dict(
    images_dir: str,
    masks_dir: str,
    segtype: str,
    name: str,
    proba_threshold: float,
    edge_dist: float,
):
    """
    Get information as a dictionnary.

    Parameters
    ----------
    images_dir : str
        Path to images to be segmented.
    masks_dir : str
        Path to images masks.
    segtype : str
        Segmentation type (eg. "fibers").
    name : str
        Name of the segmentation (eg. "green").
    proba_threshold : float < 1
        Probability threshold.
    edge_dist : float
        Distance in µm to the brain edge that is ignored.

    Returns
    -------
    params : dict

    """

    return {
        "images_location": images_dir,
        "masks_location": masks_dir,
        "type": segtype,
        "probability threshold": proba_threshold,
        "name": name,
        "edge distance": edge_dist,
    }


def write_parameters(outfile: str, parameters: dict, filters: dict):
    """
    Write parameters to `outfile`.

    A timestamp will be added. Parameters are written as key = value,
    and a [filters] is added before filters parameters.

    Parameters
    ----------
    outfile : str
        Full path to the output file.
    parameters : dict
        General parameters.
    filters : dict
        Filters parameters.

    """

    with open(outfile, "w") as fid:
        fid.writelines(f"date = {datetime.now().strftime('%d-%B-%Y %H:%M:%S')}\n")

        for key, value in parameters.items():
            fid.writelines(f"{key} = {value}\n")

        fid.writelines("[filters]\n")

        for key, value in filters.items():
            fid.writelines(f"{key} = {value}\n")


def process_directory(
    images_dir: str,
    img_suffix: str = "",
    segtype: str = "",
    target_channel: int = 0,
    proba_threshold: float = 0.0,
    qupath_class: str = "Object",
    qupath_color: list = [0, 0, 0],
    channel_suffix: str = "",
    edge_dist: float = 0.0,
    filters: dict = {},
    masks_dir: str = "",
    masks_ext: str = "",
):
    """
    Main function, processes the .ome.tiff files in the input directory.

    Parameters
    ----------
    images_dir : str
        Animal ID to process.
    img_suffix : str
        Images suffix, including extension.
    segtype : str
        Segmentation type.
    target_channel : int
        Index of the channel containning the objects of interest (eg. not the
        background), in the probability map (*not* the original images channels).
    proba_threshold : float < 1
        Probability below this value will be discarded (multiplied by `MAX_PIXEL_VALUE`)
    qupath_class : str
        Name of the QuPath classification.
    qupath_color : list of three elements
        Color associated to that classification in RGB.
    channel_suffix : str
        Channel name, will be used as a suffix in output geojson files.
    edge_dist : float
        Distance to the edge of the brain masks that will be ignored, in microns. Set to
        0 to disable this feature.
    filters : dict
        Filters values to include or excludes objects. See the top of the script.
    masks_dir : str, optional
        Path to images masks, to exclude objects found near the edges. The masks must be
        with the same name as the corresponding image to be segmented, without its
        suffix. Default is "", which disables this feature.
    masks_ext : str, optional
        Masks files extension, without leading ".". Default is ""

    """

    # -- Preparation
    # get segmentation type
    seg_method = get_seg_method(segtype)

    # get output directory path
    geojson_dir = get_geojson_dir(images_dir)

    # get images list
    images_list = [
        os.path.join(images_dir, filename)
        for filename in os.listdir(images_dir)
        if filename.endswith(img_suffix)
    ]

    # write parameters
    parameters = parameters_as_dict(
        images_dir, masks_dir, segtype, channel_suffix, proba_threshold, edge_dist
    )
    param_file = os.path.join(geojson_dir, "parameters" + channel_suffix + ".txt")
    if os.path.isfile(param_file):
        raise FileExistsError("Parameters file already exists.")
    else:
        write_parameters(param_file, parameters, filters)

    # convert parameters to pixels
    pixelsize = hq.seg.get_pixelsize(images_list[0])  # get pixel size
    edge_dist = int(edge_dist / pixelsize)
    filters = hq.seg.convert_to_pixels(filters, pixelsize)

    # get GeoJSON properties
    geojson_props = get_geojson_properties(
        qupath_class, qupath_color, objtype=QUPATH_TYPE
    )

    # -- Processing
    pbar = tqdm(images_list)
    for imgpath in pbar:
        # build file names
        imgname = os.path.basename(imgpath)
        geoname = imgname.replace(img_suffix, "")
        geojson_file = os.path.join(
            geojson_dir, geoname + "_segmentation" + channel_suffix + ".geojson"
        )

        # checks if output file already exists
        if os.path.isfile(geojson_file):
            continue

        # read images
        pbar.set_description(f"{geoname}: Loading...")
        img = tifffile.imread(imgpath, key=target_channel)
        if (edge_dist > 0) & (len(masks_dir) != 0):
            mask = tifffile.imread(os.path.join(masks_dir, geoname + "." + masks_ext))
            mask = hq.seg.pad_image(mask, img.shape)  # resize mask
            # apply mask, eroding from the edges
            img = img * hq.seg.erode_mask(mask, edge_dist)

        # image processing
        pbar.set_description(f"{geoname}: IP...")

        # threshold probability and binarization
        img = img >= proba_threshold * MAX_PIX_VALUE

        # segmentation
        pbar.set_description(f"{geoname}: Segmenting...")

        if seg_method == "lines":
            collection = hq.seg.segment_lines(
                img, geojson_props, minsize=filters["length_low"]
            )

        elif seg_method == "polygons":
            collection = hq.seg.segment_polygons(
                img,
                geojson_props,
                area_min=filters["area_low"],
                area_max=filters["area_high"],
                ecc_min=filters["ecc_low"],
                ecc_max=filters["ecc_high"],
            )

        elif seg_method == "points":
            collection = hq.seg.segment_points(
                img,
                geojson_props,
                area_min=filters["area_low"],
                area_max=filters["area_high"],
                ecc_min=filters["ecc_low"],
                ecc_max=filters["ecc_high"],
                dist_thresh=filters["dist_thresh"],
            )
        else:
            # we already printed an error message
            return

        # save geojson
        pbar.set_description(f"{geoname}: Saving...")
        with open(geojson_file, "w") as fid:
            fid.write(geojson.dumps(collection))


# --- Call
if __name__ == "__main__":
    # check parameters is a list
    if not isinstance(CHANNELS_PARAMS, (list, tuple)):
        channels_params = [CHANNELS_PARAMS]
    else:
        channels_params = CHANNELS_PARAMS

    # format suffix (append underscore or leave empty)
    if len(channels_params) == 1:

        def make_suffix(s):
            return ""
    elif len(channels_params) > 1:

        def make_suffix(s):
            return "_" + s
    else:
        raise ValueError("'CHANNELS_PARAMS' can't be empty.")

    pbar = tqdm(channels_params)
    for param in pbar:
        pbar.set_description(f"Segmenting {param["name"]}")
        process_directory(
            IMAGES_DIR,
            img_suffix=IMG_SUFFIX,
            segtype=SEGTYPE,
            target_channel=param["target_channel"],
            proba_threshold=param["proba_threshold"],
            qupath_class=param["qp_class"],
            qupath_color=param["qp_color"],
            channel_suffix=make_suffix(param["name"]),
            edge_dist=EDGE_DIST,
            filters=FILTERS.copy(),
            masks_dir=MASKS_DIR,
            masks_ext=MASKS_EXT,
        )
