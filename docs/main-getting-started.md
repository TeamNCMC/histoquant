# Getting started

## Quick start
1. Install QuPath, ABBA and miniconda3.
2. Create an environment :
```
conda create -c conda-forge -n hq python=3.12 pytables
```
3. Activate it :
```
conda activate hq
```
4. Browse to the downloaded `histoquant` folder, and install it with pip :
```
pip install .
```
If you want to build the doc :
```
pip install .[doc]
```

## Slow start
!!! tip
    If all goes well, you shouldn't need any admin rights to install the various pieces of software used before `histoquant`.

!!! danger "Important"
    Remember to cite *all* softwares you use ! See [Citing](main-citing.md).

### QuPath
QuPath is an "open source software for bioimage analysis". You can install it from the official website : [https://qupath.github.io/](https://qupath.github.io/).  
The documentation is quite clear and comprehensive : [https://qupath.readthedocs.io/en/stable/index.html](https://qupath.readthedocs.io/en/stable/index.html).

This is where you'll create QuPath projects, in which you'll be able to browse your images, annotate them, import registered brain regions and find objects of interests (via automatic segmentation, thresholding, pixel classification, ...). Then, those annotations and detections can be exported to be processed by `histoquant`.

### Aligning Big Brain and Atlases (ABBA)
This is the tool you'll use to register 2D histological sections to 3D atlases. See the [dedicated page](guide-install-abba.md).

### Python virtual environment manager (conda)
The `histoquant` package is written in Python. It depends on scientific libraries (such as [NumPy](https://numpy.org/), [pandas](https://pandas.pydata.org/) and many more). Those libraries need to be installed in versions that are compatible with each other and with `histoquant`. To make sure those versions do not conflict with other Python tools you might be using (`deeplabcut`, `abba_python`, ...), we will install `histoquant` and its dependencies in a dedicated *virtual environment*.

[conda](https://docs.conda.io/en/latest/) is a software that takes care of this. It comes with a "base" environment, from which we will create and manage other environments. It is included with the Anaconda distribution, but the latter is bloated : its "base" environment already contains tons of libraries, and tends to self-destruct at some point (eg. becomes unable to resolve the inter-dependencies), which makes you unable to install new libraries nor create new environments.

This is why it is *highly* recommended to install miniconda3 instead, a minimal installer for conda :

!!! example ""
    1. Download and install [miniconda3](https://docs.anaconda.com/miniconda/#latest-miniconda-installer-links). During the installation, choose to install for the current user, add conda to PATH and make python the default interpreter.
    2. Open a terminal (PowerShell in Windows). Run :
    ```bash
    conda init
    ```
    This will activate conda and its base environment whenever you open a new PowerShell window. Now, when opening a new PowerShell (or terminal), you should see a prompt like this :
    ```bash
    (base) PS C:\Users\myname>
    ```
    3. Run :
    ```bash
    conda config --add channels conda-forge
    ```
    Then :
    ```bash
    conda config --set channel_priority flexible
    ```
    This will make conda download the packages from the "conda-forge" online repository, which is more complete and up-to-date. The flag `-c conda-forge` in the subsequent instructions won't be necessary anymore.

!!! tip
    If Anaconda is already installed and you don't have the rights to uninstall it, you'll have to use it instead. You can launch the "Anaconda Prompt (PowerShell)", run `conda init` and follow the same instructions below (and hope it won't break in the foreseeable future).

### Installation
This section explains how to actually install the `histoquant` package.
The following commands should be run from a terminal (PowerShell). Remember that the `-c conda-forge` bits are not necessary if you did the step 3. above.

!!! example ""
    1. Create a virtual environment with python 3.12 and some libraries:
    ```
    conda create -c conda-forge -n hq python=3.12 pytables
    ```
    2. Get a copy of the `histoquant` folder, usually the latest version can be found in `Guillaume/share/programs` in the server. Copy it somewhere on your computer.
    3. We need to install it *inside* the `hq` environment we just created. First, you need to *activate* the `hq` environment :
    ```bash
    conda activate hq
    ```
    Now, the prompt should look like this :
    ```bash
    (hq) PS C:\Users\myname>
    ```
    This means that Python packages will now be installed in the `hq` environment and won't conflict with other toolboxes you might be using.
    Then, we use `pip` to install `histoquant`. `pip` was installed with Python, and will scan the `histoquant` folder, specifically the "pyproject.toml" file that lists all the required dependencies. To do so, you can either :
        +  
        ```bash
        pip install /path/to/histoquant
        ```
        + Change directory from the terminal :
        ```
        cd /path/to/histoquant
        ```
        Then install the package, "." denotes "here" :
        ```
        pip install .
        ```
        + Use the file explorer to get to the `histoquant` folder, use ++shift+right-button++ to "Open PowerShell window here" and run :
        ```
        pip install .
        ```

`histoquant` is now installed inside the `hq` environment and will be available in Python from that environment !

!!! tip
    You will need to perform step 3. each time you want to update the package.

If you already have registered data and cells in QuPath, you can export Annotations and Detections as TSV files and head to the [Example](main-using-notebooks.md) section.