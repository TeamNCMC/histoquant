"""
Script to call QuPath export_classifier groovy script, multi-threaded.

Remember to edit the relevant groovy script beforehand. Remember that QuPath itself is
multithreaded, so spare some resources.

Fill-in the parameters below and run the script.
The QuPath project is expected to be in data/AnimalID/animalid_qupath_scope
The `QPROJ_PATH` variable can be overridden directly.

"""

import os

from cuisto.tools import qupath_script_runner as qsr

# --- Parameters
ANIMAL = "mouse0"
SCOPE = "full"

NTHREADS = 6
QUIET = True

# To exclude already exported probability maps
lfiles = [
    name.replace("_Probabilities", ".ome")
    for name in os.listdir(
        "/path/to/data/mouse0/mouse0_segmentation/fibers/probabilities"
    )
]
EXCLUDE_LIST = lfiles

WDIR = "/path/to/data"  # root data directory
# look for a QuPath project in WDIR/ANIMAL/animal_qupath_SCOPE
QPROJ_PATH = os.path.join(
    WDIR, ANIMAL, ANIMAL.lower() + "_qupath_" + SCOPE, "project.qpproj"
)
SCRIPT_PATH = "../qupath-utils/segmentation/exportPixelClassifierProbabilities"
QUPATH_EXE = "C:/Users/USERNAME/AppData/Local/QuPath-0.5.1/QuPath-0.5.1 (console).exe"

# --- Call ---
if __name__ == "__main__":
    qsr.multirun(
        QUPATH_EXE,
        SCRIPT_PATH,
        QPROJ_PATH,
        quiet=QUIET,
        nthreads=NTHREADS,
        exclude_list=EXCLUDE_LIST,
    )
