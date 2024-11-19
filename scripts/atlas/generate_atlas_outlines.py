"""
Script to generate atlas outlines in sagittal, cornal and horizontal views, with each
regions of the Allen Brain Atlas in a single HDF5 file.

"""

import h5py
import numpy as np
from brainglobe_atlasapi import BrainGlobeAtlas
from skimage import measure
from tqdm import tqdm

# --- Parameters
out_file = "/path/to/allen_cord_20um_outlines.h5"
atlas_name = "allen_cord_20um"

atlas = BrainGlobeAtlas(atlas_name, check_latest=False)


# --- Preparation
def get_structure_contour(mask: np.ndarray, axis: int = 2) -> list:
    """
    Get structure contour.

    Parameters
    ----------
    mask : np.ndarray
        3D mask of structure.
    axis : int, optional
        Axis, determines the projection. 2 is sagittal. Default is 2.

    Returns
    -------
    contour : list
        List of 2D array with contours (in pixels).

    """
    return measure.find_contours(np.max(mask, axis=axis))


def outlines_to_group(
    grp, acronym: str, outlines: list, resolution: tuple = (10, 10), fliplr=False
):
    """
    Write arrays to hdf5 group.

    Parameters
    ----------
    grp : h5py group
        Group in hdf5 file
    structure : str
        Subgroup name
    outlines : list
        List of 2D ndarrays
    resolution : tuple, optional
        Resolution (row, columns) in the 2D projection, before flipping. Default is
        (10, 10).
    fliplr : bool, Defaults to False

    """
    grp_structure = grp.create_group(acronym)
    c = 0
    for outline in outlines:
        outline *= resolution
        if fliplr:
            outline = np.fliplr(outline)
        grp_structure.create_dataset(f"{c}", data=outline)
        c += 1


# --- Processing
with h5py.File(out_file, "w") as f:
    # create groups
    grp_sagittal = f.create_group("sagittal")
    grp_coronal = f.create_group("coronal")
    grp_top = f.create_group("top")

    # loop through structures
    pbar = tqdm(atlas.structures_list)
    for structure in pbar:
        pbar.set_description(structure["acronym"])

        mask = atlas.get_structure_mask(structure["id"])

        # sagittal
        outlines = get_structure_contour(mask, axis=2)
        res = atlas.resolution[1], atlas.resolution[0]  # d-v, r-c
        outlines_to_group(grp_sagittal, structure["acronym"], outlines, resolution=res)

        # coronal
        outlines = get_structure_contour(mask, axis=0)
        res = atlas.resolution[1], atlas.resolution[2]  # d-v, l-r
        outlines_to_group(
            grp_coronal, structure["acronym"], outlines, resolution=res, fliplr=True
        )

        # top
        outlines = get_structure_contour(mask, axis=1)
        res = atlas.resolution[2], atlas.resolution[0]  # l-r, a-p
        outlines_to_group(grp_top, structure["acronym"], outlines, resolution=res)
