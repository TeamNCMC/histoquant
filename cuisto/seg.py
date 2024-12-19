"""seg module, part of cuisto.

Functions for segmentating probability map stored as an image.

"""

import uuid

import geojson
import numpy as np
import pandas as pd
import shapely
import tifffile
from skan import Skeleton, summarize
from skimage import measure, morphology


def get_pixelsize(image_name: str) -> float:
    """
    Get pixel size recorded in `image_name` TIFF metadata.

    Parameters
    ----------
    image_name : str
        Full path to image.

    Returns
    -------
    pixelsize : float
        Pixel size in microns.

    """

    with tifffile.TiffFile(image_name) as tif:
        # XResolution is a tuple, numerator, denomitor. The inverse is the pixel size
        return (
            tif.pages[0].tags["XResolution"].value[1]
            / tif.pages[0].tags["XResolution"].value[0]
        )


def convert_to_pixels(filters, pixelsize):
    """
    Convert some values in `filters` in pixels.

    Parameters
    ----------
    filters : dict
        Must contain the keys used below.
    pixelsize : float
        Pixel size in microns.

    Returns
    -------
    filters : dict
        Same as input, with values in pixels.

    """

    filters["area_low"] = filters["area_low"] / pixelsize**2
    filters["area_high"] = filters["area_high"] / pixelsize**2
    filters["length_low"] = filters["length_low"] / pixelsize
    filters["dist_thresh"] = int(filters["dist_thresh"] / pixelsize)

    return filters


def pad_image(img: np.ndarray, finalsize: tuple | list) -> np.ndarray:
    """
    Pad image with zeroes to match expected final size.

    Parameters
    ----------
    img : ndarray
    finalsize : tuple or list
        nrows, ncolumns

    Returns
    -------
    imgpad : ndarray
        img with black borders.

    """

    final_h = finalsize[0]  # requested number of rows (height)
    final_w = finalsize[1]  # requested number of columns (width)
    original_h = img.shape[0]  # input number of rows
    original_w = img.shape[1]  # input number of columns

    a = (final_h - original_h) // 2  # vertical padding before
    aa = final_h - a - original_h  # vertical padding after
    b = (final_w - original_w) // 2  # horizontal padding before
    bb = final_w - b - original_w  # horizontal padding after

    return np.pad(img, pad_width=((a, aa), (b, bb)), mode="constant")


def erode_mask(mask: np.ndarray, edge_dist: float) -> np.ndarray:
    """
    Erode the mask outline so that is is `edge_dist` smaller from the border.

    This allows discarding the edges.

    Parameters
    ----------
    mask : ndarray
    edge_dist : float
        Distance to edges, in pixels.

    Returns
    -------
    eroded_mask : ndarray of bool

    """

    if edge_dist % 2 == 0:
        edge_dist += 1  # decomposition requires even number

    footprint = morphology.square(edge_dist, decomposition="sequence")

    return mask * morphology.binary_erosion(mask, footprint=footprint)


def get_image_skeleton(img: np.ndarray, minsize=0) -> np.ndarray:
    """
    Get the image skeleton.

    Computes the image skeleton and removes objects smaller than `minsize`.

    Parameters
    ----------
    img : ndarray of bool
    minsize : number, optional
        Min. size the object can have, as a number of pixels. Default is 0.

    Returns
    -------
    skel : ndarray of bool
        Binary image with 1-pixel wide skeleton.

    """

    skel = morphology.skeletonize(img)

    return morphology.remove_small_objects(skel, min_size=minsize, connectivity=2)


def get_collection_from_skel(
    skeleton: Skeleton, properties: dict, rescale_factor: float = 1.0, offset=0.5
) -> geojson.FeatureCollection:
    """
    Get the coordinates of each skeleton path as a GeoJSON Features in a
    FeatureCollection.
    `properties` is a dictionnary with QuPath properties of each detections.

    Parameters
    ----------
    skeleton : skan.Skeleton
    properties : dict
        QuPatj objects' properties.
    rescale_factor : float
        Rescale output coordinates by this factor.
    offset : float
        Shift coordinates by this amount, typically to get pixel centers or edges.
        Default is 0.5.

    Returns
    -------
    collection : geojson.FeatureCollection
        A FeatureCollection ready to be written as geojson.

    """

    branch_data = summarize(skeleton, separator="_")

    collection = []
    for ind in range(skeleton.n_paths):
        prop = properties.copy()
        prop["measurements"] = {"skeleton_id": int(branch_data.loc[ind, "skeleton_id"])}
        collection.append(
            geojson.Feature(
                geometry=shapely.LineString(
                    (skeleton.path_coordinates(ind)[:, ::-1] + offset) * rescale_factor
                ),  # shape object
                properties=prop,  # object properties
                id=str(uuid.uuid4()),  # object uuid
            )
        )

    return geojson.FeatureCollection(collection)


def get_collection_from_poly(
    contours: list, properties: dict, rescale_factor: float = 1.0, offset: float = 0.5
) -> geojson.FeatureCollection:
    """
    Gather coordinates in the list and put them in GeoJSON format as Polygons.

    An entry in `contours` must define a closed polygon. `properties` is a dictionnary
    with QuPath properties of each detections.

    Parameters
    ----------
    contours : list
    properties : dict
        QuPatj objects' properties.
    rescale_factor : float
        Rescale output coordinates by this factor.
    offset : float
        Shift coordinates by this amount, typically to get pixel centers or edges.
        Default is 0.5.

    Returns
    -------
    collection : geojson.FeatureCollection
        A FeatureCollection ready to be written as geojson.

    """
    collection = [
        geojson.Feature(
            geometry=shapely.Polygon(
                np.fliplr((contour + offset) * rescale_factor)
            ),  # shape object
            properties=properties,  # object properties
            id=str(uuid.uuid4()),  # object uuid
        )
        for contour in contours
    ]

    return geojson.FeatureCollection(collection)


def get_collection_from_points(
    coords: list, properties: dict, rescale_factor: float = 1.0, offset: float = 0.5
) -> geojson.FeatureCollection:
    """
    Gather coordinates from `coords` and put them in GeoJSON format.

    An entry in `coords` are pairs of (x, y) coordinates defining the point.
    `properties` is a dictionnary with QuPath properties of each detections.

    Parameters
    ----------
    coords : list
    properties : dict
    rescale_factor : float
        Rescale output coordinates by this factor.

    Returns
    -------
    collection : geojson.FeatureCollection

    """

    collection = [
        geojson.Feature(
            geometry=shapely.Point(
                np.flip((coord + offset) * rescale_factor)
            ),  # shape object
            properties=properties,  # object properties
            id=str(uuid.uuid4()),  # object uuid
        )
        for coord in coords
    ]

    return geojson.FeatureCollection(collection)


def segment_lines(
    img: np.ndarray, geojson_props: dict, minsize=0.0, rescale_factor=1.0
) -> geojson.FeatureCollection:
    """
    Wraps skeleton analysis to get paths coordinates.

    Parameters
    ----------
    img : ndarray of bool
        Binary image to segment as lines.
    geojson_props : dict
        GeoJSON properties of objects.
    minsize : float
        Minimum size in pixels for an object.
    rescale_factor : float
        Rescale output coordinates by this factor.

    Returns
    -------
    collection : geojson.FeatureCollection
        A FeatureCollection ready to be written as geojson.

    """

    skel = get_image_skeleton(img, minsize=minsize)

    # get paths coordinates as FeatureCollection
    skeleton = Skeleton(skel, keep_images=False)
    return get_collection_from_skel(
        skeleton, geojson_props, rescale_factor=rescale_factor
    )


def segment_polygons(
    img: np.ndarray,
    geojson_props: dict,
    area_min: float = 0.0,
    area_max: float = np.inf,
    ecc_min: float = 0.0,
    ecc_max: float = 1.0,
    rescale_factor: float = 1.0,
) -> geojson.FeatureCollection:
    """
    Polygon segmentation.

    Parameters
    ----------
    img : ndarray of bool
        Binary image to segment as polygons.
    geojson_props : dict
        GeoJSON properties of objects.
    area_min, area_max : float
        Minimum and maximum area in pixels for an object.
    ecc_min, ecc_max : float
        Minimum and maximum eccentricity for an object.
    rescale_factor: float
        Rescale output coordinates by this factor.

    Returns
    -------
    collection : geojson.FeatureCollection
        A FeatureCollection ready to be written as geojson.

    """

    label_image = measure.label(img)

    # get objects properties
    stats = pd.DataFrame(
        measure.regionprops_table(
            label_image, properties=("label", "area", "eccentricity")
        )
    )

    # remove objects not matching filters
    toremove = stats[
        (stats["area"] < area_min)
        | (stats["area"] > area_max)
        | (stats["eccentricity"] < ecc_min)
        | (stats["eccentricity"] > ecc_max)
    ]

    label_image[np.isin(label_image, toremove["label"])] = 0

    # find objects countours
    label_image = label_image > 0
    contours = measure.find_contours(label_image)

    return get_collection_from_poly(
        contours, geojson_props, rescale_factor=rescale_factor
    )


def segment_points(
    img: np.ndarray,
    geojson_props: dict,
    area_min: float = 0.0,
    area_max: float = np.inf,
    ecc_min: float = 0,
    ecc_max: float = 1,
    dist_thresh: float = 0,
    rescale_factor: float = 1,
) -> geojson.FeatureCollection:
    """
    Point segmentation.

    First, segment polygons to apply shape filters, then extract their centroids,
    and remove isolated points as defined by `dist_thresh`.

    Parameters
    ----------
    img : ndarray of bool
        Binary image to segment as points.
    geojson_props : dict
        GeoJSON properties of objects.
    area_min, area_max : float
        Minimum and maximum area in pixels for an object.
    ecc_min, ecc_max : float
        Minimum and maximum eccentricity for an object.
    dist_thresh : float
        Maximal distance in pixels between objects before considering them as isolated and remove them.
        0 disables it.
    rescale_factor : float
        Rescale output coordinates by this factor.

    Returns
    -------
    collection : geojson.FeatureCollection
        A FeatureCollection ready to be written as geojson.

    """

    # get objects properties
    stats = pd.DataFrame(
        measure.regionprops_table(
            measure.label(img), properties=("label", "area", "eccentricity", "centroid")
        )
    )

    # keep objects matching filters
    stats = stats[
        (stats["area"] >= area_min)
        & (stats["area"] <= area_max)
        & (stats["eccentricity"] >= ecc_min)
        & (stats["eccentricity"] <= ecc_max)
    ]

    # create an image from centroids only
    stats["centroid-0"] = stats["centroid-0"].astype(int)
    stats["centroid-1"] = stats["centroid-1"].astype(int)
    bw = np.zeros(img.shape, dtype=bool)
    bw[stats["centroid-0"], stats["centroid-1"]] = True

    # filter isolated objects
    if dist_thresh:
        # dilation of points
        if dist_thresh % 2 == 0:
            dist_thresh += 1  # decomposition requires even number

        footprint = morphology.square(int(dist_thresh), decomposition="sequence")
        dilated = measure.label(morphology.binary_dilation(bw, footprint=footprint))
        stats = pd.DataFrame(
            measure.regionprops_table(dilated, properties=("label", "area"))
        )

        # objects that did not merge are alone
        toremove = stats[(stats["area"] <= dist_thresh**2)]
        dilated[np.isin(dilated, toremove["label"])] = 0  # remove them

        # apply mask
        bw = bw * dilated

    # get points coordinates
    coords = np.argwhere(bw)

    return get_collection_from_points(
        coords, geojson_props, rescale_factor=rescale_factor
    )
