"""
Run a QuPath script in a parallel loop.

Requires paquo to get the list of images.

"""

import os
import multiprocessing
import subprocess

from functools import partial
from paquo.projects import QuPathProject
from tqdm import tqdm

NTHREADS = int(os.cpu_count() / 2)


def get_images_list(qupath_project: str) -> list[str]:
    """
    Get the QuPath project images list.

    Parameters
    ----------
    qupath_project : str
        Full path the project.qpproj file.

    Returns
    -------
    images_list : list of str
        List of images names.

    """

    qp = QuPathProject(qupath_project, "r")
    return [img.image_name for img in qp.images]


def run_script(
    qupath_exe: str,
    script_path: str,
    qupath_project: str,
    quiet: bool,
    save: bool,
    imgname: str,
):
    """
    Run groovy script with QuPath in console mode on selected image.

    Parameters
    ----------
    qupath_exe : str
        Full path to the QuPath console exe.
    script_path : str
        Full path to the groovy script to be executed.
    qupath_project : str
        Full path to the QuPath .qproj file.
    quiet : bool
        Suppress console verbose. Default is False.
    save : bool, optional
        Update data files for each image in the project. Default is False.
    imgname : str
        Image name in the QuPath project.
    """

    if quiet:
        stdout = subprocess.DEVNULL
        log = "OFF"
    else:
        stdout = None
        log = "INFO"

    if save:
        save_arg = "-s"
    else:
        save_arg = ""

    cmd = [
        qupath_exe,
        "--quiet",
        "--log",
        log,
        "script",
        script_path,
        "-p",
        qupath_project,
        "-i",
        imgname,
        save_arg,
    ]
    subprocess.run(cmd, shell=True, stdout=stdout)


def multirun(
    qupath_exe: str,
    script_path: str,
    qupath_project: str,
    quiet: bool = False,
    save: bool = False,
    nthreads: int = NTHREADS,
    exclude_list: list[str] = [],
):
    """
    Run groovy script on QuPath project images, in multi-thread.

    Parameters
    ----------
    qupath_exe : str
        Full path to the QuPath console exe.
    script_path : str
        Full path to the groovy script to be executed.
    qupath_project : str
        Full path to the QuPath .qproj file.
    quiet : bool, optional
        Suppress console verbose. Default is False.
    save : bool, optional
        Update data files for each image in the project. Default is False.
    nthreads : int, optional
        Number of threads. Default is half the number of cores of the computer.
    exclude_list : list[str], optional
        List of images name to NOT execute the script on. Default is empty list.

    """

    # get list of images
    imglist = get_images_list(qupath_project)
    # exclude specified images
    imglist = [imgname for imgname in imglist if imgname not in exclude_list]

    # multithreaded call to the script via QuPath console
    with multiprocessing.Pool(nthreads) as pool:
        # prepare the lazy map
        runner = tqdm(
            pool.imap(
                partial(run_script, qupath_exe, script_path, qupath_project, quiet, save),
                imglist,
            ),
            total=len(imglist),
        )

        # execute
        tuple(runner)
