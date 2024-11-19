"""
Template to show how to run groovy script with QuPath, multi-threaded.
"""

import histoquant.tools.qupath_script_runner as qsr

# --- Parameters
QPROJ_PATH = "/path/to/qupath/project.qproj"
"""Full path to the QuPath project."""
NTHREADS = 5
"""Number of threads to use."""
QUIET = True
"""Use QuPath in quiet mode, eg. with minimal verbosity."""
SAVE = True
"""Whether to save the project after the script ran on an image."""
EXCLUDE_LIST = []
"""Images names to NOT run the script on."""
SCRIPT_PATH = "/path/to/the/script.groovy"
"""Path to the groovy script."""
QUPATH_EXE = "/path/to/the/qupath/QuPath-0.5.1 (console).exe"
"""Path to the QuPath executable (console mode)."""

# --- Call ---
if __name__ == "__main__":
    qsr.multirun(
        QUPATH_EXE,
        SCRIPT_PATH,
        QPROJ_PATH,
        quiet=QUIET,
        save=SAVE,
        nthreads=NTHREADS,
        exclude_list=EXCLUDE_LIST,
    )
