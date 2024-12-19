# Create pyramidal OME-TIFF

This page will guide you to use the `pyramid-creator` package, in the event the CZI file does not work directly in QuPath. The script will generate [pyramids](tips-formats.md#pyramids) from OME-TIFF files exported from ZEN.

!!! tip inline end
    `pyramid-creator` can also pyramidalize images using Python only with the `--no-use-qupath` option.
This Python script uses QuPath under the hood, via a companion script called `createPyramids.groovy`. It will find the OME-TIFF files and make QuPath run the groovy script on it, in console mode (without graphical user interface).

This script is standalone, eg. it does not rely on the `cuisto` package. But installing the later makes sure all dependencies are installed (namely `typer` and `tqdm` with the QuPath backend and quite a few more for the Python backend).

`pyramid-creator` moved to a standalone package that you can find [here](https://github.com/TeamNCMC/pyramid-creator#pyramid_creator) with [installation](https://github.com/TeamNCMC/pyramid-creator#install) and [usage](https://github.com/TeamNCMC/pyramid-creator#usage) instructions.

## Installation
You will find instructions on the dedicated project page over at [Github](https://github.com/TeamNCMC/pyramid-creator#pyramid_creator).

For reference :

You will need `conda`, follow [those instructions](main-getting-started.md#python-virtual-environment-manager-conda) to install it.

Then, create a virtual environment if you didn't already (`pyramid-creator` can be installed in the environment for `cuisto`) and install the [`pyramid-creator`](https://github.com/TeamNCMC/pyramid-creator) package.
```bash
conda create -c conda-forge -n cuisto-env python=3.12  # not required if you already create an environment
conda activate cuisto-env
pip install pyramid-creator
```
To use the Python backend (with `tifffile`), replace the last line with :
```
pip install pyramid-creator[python-backend]
```
To use the QuPath backend, a working QuPath installation is required, and the `pyramid-creator` command needs to be aware of its location.

To do so, first, install [QuPath](https://qupath.github.io). By default, it will install in `~\AppData\QuPath-0.X.Y`. In any case, note down the installation location.

Then, you have several options :
- Create a file in your user directory called "QUPATH_PATH" (without extension), containing the full path to the QuPath console executable. In my case, it reads : `C:\Users\glegoc\AppData\Local\QuPath-0.5.1\QuPath-0.5.1 (console).exe`. Then, the `pyramid-creator` script will read this file to find the QuPath executable.
- Specify the QuPath path as an option when calling the command line interface (see the [Usage](#usage) section) :
```bash
pyramid-creator /path/to/your/images --qupath-path "C:\Users\glegoc\AppData\Local\QuPath-0.5.1\QuPath-0.5.1 (console).exe"
```
- Specify the QuPath path as an option when using the package in a Python script (see the [Usage](#usage) section) :
```python
from pyramid_creator import pyramidalize_directory
pyramidalize_directory("/path/to/your/images/", qupath_path="C:\Users\glegoc\AppData\Local\QuPath-0.5.1\QuPath-0.5.1 (console).exe")
```
- If you're using Windows, using QuPath v0.6.0, v0.5.1 or v0.5.0 and chose the default installation location, `pyramid-creator` *should* find it automatically and write it down in the "QUPATH_PATH" file by itself.

## Export CZI to OME-TIFF
[OME-TIFF](https://ome-model.readthedocs.io/en/stable/ome-tiff/) is a specification of the TIFF image format. It specifies how the metadata should be written to the file to be interoperable between softwares. ZEN can export to OME-TIFF so you don't need to pay attention to [metadata](tips-formats.md#metadata). Therefore, you won't need to specify pixel size and channels names and colors as it will be read directly from the OME-TIFF files.
!!! example ""
    1. Open your CZI file in ZEN.
    2. Open the "Processing tab" on the left panel.
    3. Under method, choose Export/Import > OME TIFF-Export.
    4. In Parameters, make sure to tick the "Show all" tiny box on the right.
    5. The following parameters should be used (checked), the other should be *unchecked* :
        - Use Tiles
        - Original data :warning: "Convert to 8 Bit" should be **UNCHECKED** :warning:
        - OME-XML Scheme : 2016-06
        - Use full set of dimensions (unless you want to select slices and/or channels)
    6. In Input, choose your file
    7. Go back to Parameters to choose the output directory and file prefix. "_s1", "_s2"... will be appended to the prefix.
    8. Back on the top, click the "Apply" button.

The OME-TIFF files should be ready to be pyramidalized with the `create_pyramids.py` script.

## Usage
See the instructions on the dedicated project page over at [Github](https://github.com/TeamNCMC/pyramid-creator#pyramid_creator).
