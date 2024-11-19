"""
Script to generate an animation with brain regions in 3D and objects.
"""

import os
import random

import brainrender
import numpy as np
import pandas as pd
import vedo
from brainrender import Animation, Scene
from brainrender.actors import Points, PointsDensity

vedo.settings.default_backend = "vtk"

# --- Parameters
# detections location
DETECTIONS_FILE = "/path/to/measurements_detections.tsv"
# output file
OUT = "/path/to/output/video.mp4"
# classifications to show in different colors
CLASSIFICATIONS_NAMES = ["Cells: marker-", "Cells: marker+"]
# associated colors
CLASSIFICATIONS_COLORS = ["#960010", "#1c9e5e"]
# regions to show (root will always be shown)
REGIONS_NAMES = ["GRN", "V", "VII", "XII", "RN", "NPC", "RPF"]
# objects size (will be sphere with this radius)
CELLS_RADIUS = 20
# whether to show regions labels
DISP_LABELS = False
# whether to show density heatmap
DISP_DENSITY = False
# density radius
DENSITY_RADIUS = 200

# rendering camera view
CUSTOM_CAMERA = dict(
    pos=(34534.9, 7321.81, -5757.58),
    viewup=(0, -1.00000, 0),
    clipping_range=(12684.8, 46870.5),
)
# "sagittal", "sagittal2", "frontal", "top", "top_side", "three_quarters"

# brainrender options
brainrender.settings.SHOW_AXES = False


# --- Functions
def get_random_colors(ncolors):
    """
    Generates ncolors colors returned as hex.

    Parameters
    ----------
    ncolors : int, number of colors

    Returns :
    -------
    list of ncolors hex code for random colors.
    """

    colors = []
    for _ in range(0, ncolors):
        colors.append(hex(random.randrange(0, 2**24)).replace("0x", "#"))

    return colors


def get_coords(df: pd.DataFrame, tomicrons: bool = True):
    dfc = df.copy()

    if tomicrons:
        conv = 1000
    else:
        conv = 1

    return np.array(
        [
            dfc["Atlas_X"].to_numpy() * conv,
            dfc["Atlas_Y"].to_numpy() * conv,
            dfc["Atlas_Z"].to_numpy() * conv,
        ]
    ).T


def create_video(
    file: str,
    out: str,
    classifications_names: list,
    classifications_colors: list,
    regions_names: list,
    cells_radius: int | float,
    disp_labels: bool = False,
    disp_density: bool = False,
    density_radius: int | float = 200,
):
    """
    Create animation of objects in the brain.
    """
    # read file
    df = pd.read_csv(file, index_col="Object ID", sep="\t")

    # get cells coordinates
    coords_list = [
        get_coords(df[df["Classification"] == classification])
        for classification in classifications_names
    ]

    # make a Scene
    scene = Scene()

    # get some random colors to color regions
    colors = get_random_colors(len(regions_names))

    # add brain regions
    regions = [
        scene.add_brain_region(region, color=color, alpha=0.1, silhouette=True)
        for region, color in zip(regions_names, colors)
    ]

    # add brain regions labels
    if disp_labels:
        _ = [
            scene.add_label(
                reg, name, size=300, radius=50, xoffset=0, yoffset=0, zoffset=0
            )
            for reg, name in zip(regions, regions_names)
        ]

    # add cells
    for coords, color in zip(coords_list, classifications_colors):
        points = Points(
            coords, name="cell", colors=color, alpha=0.5, radius=cells_radius
        )
        scene.add(points)

    # add density
    if disp_density:
        voldensity = PointsDensity(np.concat(coords_list), radius=density_radius)
        voldensity.add_scalarbar3d(
            title=f"Density (counts in r_s ={density_radius})",
            italic=1,
            label_rotation=180,
        )
        scene.add(voldensity)

    # get file parts
    out_dir = os.path.dirname(out)
    out_file = os.path.basename(out).replace(".mp4", "")

    # make video
    anim = Animation(scene, out_dir, out_file)

    anim.add_keyframe(0, camera="sagittal", zoom=1.2)
    anim.add_keyframe(3, camera="top_side", zoom=1.1)
    anim.add_keyframe(6, camera="three_quarters", zoom=1.2)
    anim.add_keyframe(9, camera=CUSTOM_CAMERA, zoom=1.2)

    anim.make_video(duration=12, fps=20, resetcam=True)


if __name__ == "__main__":
    create_video(
        DETECTIONS_FILE,
        OUT,
        CLASSIFICATIONS_NAMES,
        CLASSIFICATIONS_COLORS,
        REGIONS_NAMES,
        CELLS_RADIUS,
        disp_labels=DISP_LABELS,
        disp_density=DISP_DENSITY,
        density_radius=DENSITY_RADIUS,
    )
