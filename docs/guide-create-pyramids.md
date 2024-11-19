# Create pyramidal OME-TIFF

This page will guide you to use the `create_pyramids` script, in the event the CZI file does not work directly in QuPath. The script will generate [pyramids](tips-formats.md#pyramids) from OME-TIFF files exported from ZEN.

!!! tip inline end
    The `create_pyramids.py` script can also pyramidalize images using Python only with the `--no-use-qupath` option, but I find it slower and less reliable.
This Python script uses QuPath under the hood, via a companion script called `createPyramids.groovy`. It will find the OME-TIFF files and make QuPath run the groovy script on it, in console mode (without graphical user interface).

This script is standalone, eg. it does not rely on the `histoquant` package. But installing the later makes sure all dependencies are installed (namely `typer` and `tqdm` with the QuPath backend and quite a few more for the Python backend).

## Installation
You will need a virtual environment with the required dependencies.

Follow [those instructions](main-getting-started.md#python-virtual-environment-manager-conda) to install miniconda3 if you didn't already.

Then, install the required dependencies.
=== "Recommended"
    Install the `histoquant` package by following [those instructions](main-getting-started.md#installation).
=== "Minimal"
    Alternatively, if you don't plan to use the `histoquant` package, you can create a minimal conda environment with only the libraries required for `create_pyramids.py`.
    ```bash title="With QuPath backend"
    conda create -n hq python=3.12
    conda activate hq
    pip install typer tqdm
    ```
    ```bash title="With Python backend"
    conda create -n hq python=3.12
    conda activate hq
    pip install typer tqdm numpy tifffile scikit-image
    ```
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
The script is located under `scripts/pyramids`. Copy the two files (.py and .groovy) elsewhere on your computer.

To use the QuPath backend (recommended), you need to set its path in the script. To do so, open the `create_pyramids.py` file with a text editor (Notepad or [vscode](https://code.visualstudio.com/) to get nice syntax coloring).
Locate the `QUPATH_PATH` line :
``` python linenums="47" hl_lines="2-4"
--8<-- "scripts/pyramids/create_pyramids.py:47:51"
```

!!! info inline end
    The AppData directory is hidden by default. In the file explorer, you can go to the "View" tab and check "Hidden items" under "Show/hide".
And replace the path to the "QuPath-0.X.Y (console).exe" executable. QuPath should be installed in `C:\Users\USERNAME\AppData\Local\QuPath-0.X.Y\` by default.  
Save the file. Then run the script on your images :

!!! example ""
    1. Open a terminal (PowerShell) so that it can find the `create_pyramids.py` script, by either :
        - open PowerShell from the start menu, then browse to the location of your script:
        ```bash
        cd /path/to/your/scripts
        ```
        - From the file explorer, browse to where the script is and in an empty space, ++shift+right-button++ to "Open PowerShell window here"
    2. Activate the virtual environment :
    ```bash
    conda activate hq
    ```
    3. Copy the path to your OME-TIFF images (for example "D:\Data\Histo\NiceMouseName\NiceMouseName-tiff\")
    4. In the terminal, run the script on your images :
    ```bash
    python create_pyramids.py "D:\Data\Histo\NiceMouseName\NiceMouseName-tiff\"
    ```
    !!! warning
        Make sure to use **double quotes** when specifying the path (**"**D:\some\path**"**), because if there are whitespaces in it, each whitespace-separated bits will be parsed as several arguments for the script.

!!! tip
    `create_pyramids.py` can behave like a command line interface. In the event you would need to modify the default values used in the script (tile size and the like), you can either edit the script or, preferably, use options when calling the script like so :
    ```bash
    python create_pyramids.py --OPTION VALUE /path/to/images
    ```
    Learn more by asking for help :
    ```bash
    python create_pyramids.py --help
    ```

Upon completion, this will create a subdirectory "pyramidal" next to your OME-TIFF files where you will find the pyramidal images ready to be used in QuPath and ABBA. You can safely delete the original OME-TIFF exported from ZEN.

You can check the API documentation for this script [here](api-script-pyramids.md).