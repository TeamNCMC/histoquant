# Install ABBA
You can head to [the ABBA documentation](https://abba-documentation.readthedocs.io/en/latest/installation/installation.html#) for installation instructions. You'll see that a Windows installer is available. While it might be working great, I prefer to do it manually step-by-step to make sure everything is going well.

You will find below installation instructions for the regular [ABBA Fiji plugin](#abba-fiji), which proposes only the mouse and rat brain atlases. To be able to use the [Brainglobe atlases](https://brainglobe.info/documentation/brainglobe-atlasapi/usage/atlas-details.html#available-atlases), you will need the [Python version](#abba-python). The two can be installed alongside each other.

## ABBA Fiji
### Install Fiji
Install the "batteries-included" distribution of ImageJ, Fiji, from the [official website](https://fiji.sc/).  
!!! warning inline end
    Extract Fiji somewhere you have write access, otherwise Fiji will not be able to download and install plugins. In other words, put the folder in your User directory and *not* in C:\, C:\Program Files and the like.

1. Download the zip archive and extract it somewhere relevant.
2. Launch ImageJ.exe.

### Install the ABBA plugin
We need to add the PTBIOP update site, managed by the bio-imaging and optics facility at EPFL, that contains the ABBA plugin.

1. In Fiji, head to `Help > Update`...  
2. In the ImageJ updater window, click on `Manage Update Sites`. Look up `PTBIOP`, and click on the check box. `Apply and Close`, and `Apply Changes`.
This will download and install the required plugins. Restart ImageJ as suggested.  
3. In Fiji, head to `Plugins > BIOP > Atlas > ABBA - ABBA start`, or simply type `abba start` in the search box.  
Choose the "Adult Mouse Brain - Allen Brain Atlas V3p1". It will download this atlas and might take a while, depending on your Internet connection.

### Install the automatic registration tools
ABBA can leverage the [elastix toolbox](https://elastix.dev/) for automatic 2D in-plane registration. 

1. You need to download it [here](https://elastix.dev/download.php), which will redirect you to the Github releases page (5.2.0 should work).  
2. Download the zip archive and extract it somewhere relevant.  
3. In Fiji, in the search box, type "set and check" and launch the "Set and Check Wrappers" command. Set the paths to "elastix.exe" and "transformix.exe" you just downloaded.

ABBA should be installed and functional ! You can check the [official documentation](https://abba-documentation.readthedocs.io/en/latest/index.html) for usage instructions and some tips [here](tips-abba.md).

## ABBA Python
[Brainglobe](https://brainglobe.info/) is an initiative aiming at providing interoperable, model-agnostic Python-based tools for neuroanatomy. They package various published volumetric anatomical atlases of different species (check the [list](https://brainglobe.info/documentation/brainglobe-atlasapi/usage/atlas-details.html#available-atlases)), including the Allen Mouse brain atlas (CCFv3, [ref.](https://doi.org/10.1016/j.cell.2020.04.007)) and a 3D version of the Allen mouse spinal cord atlas ([ref](https://doi.org/10.1016/j.crmeth.2021.100074)).

To be able to leverage those atlases, we need to make ImageJ and Python be able to talk to each other. This is the purpose of [abba_python](https://github.com/BIOP/abba_python), that will install ImageJ and its ABBA plugins *inside* a python environment, with bindings between the two worlds.

### Install `conda`
If not done already, follow [those instructions](main-getting-started.md#python-virtual-environment-manager-conda) to install `conda`.

### Install abba_python in a virtual environment
1. Open a terminal (PowerShell).
2. Create a virtual environment with Python 3.10, OpenJDK and PyImageJ :
```
conda create -c conda-forge -n abba_python python=3.10 openjdk=11 maven pyimagej notebook
```
3. Install the latest functional version of abba_python with pip :
```
pip install abba-python==0.9.6.dev0
```
4. Restart the terminal and activate the new environment :
```
conda activate abba_python
```
5. Download the Brainglobe atlas you want (eg. Allen mouse spinal cord) :
```
brainglobe install -a allen_cord_20um
```
6. Launch an interactive Python shell :
```
ipython
```
You should see the IPython prompt, that looks like this :
```
In [1]:
```
7. Import abba_python and launch ImageJ from Python :
```
from abba_python import abba
abba.start_imagej()
```
The first launch needs to initialize ImageJ and install all required plugins, which takes a while (>5min).
8. Use ABBA as the regular Fiji version ! The main difference is that the dropdown menu to select which atlas to use is populated with the Brainglobe atlases.

!!! tip
    Afterwards, to launch ImageJ from Python and do some registration work, you just need to launch a terminal (PowerShell), and do steps 4., 6., and 7.

### Install the automatic registration tools
You can follow the [same instructions](#install-the-automatic-registration-tools) as the regular Fiji version. You can do it from either the "normal" Fiji or the ImageJ instance launched from Python, they share the same configuration files. Therefore, if you already did it in regular Fiji, elastix should already be set up and ready to use in ImageJ from Python.

### Troubleshooting
#### JAVA_HOME errors
Unfortunately on some computers, Python does not find the Java virtual machine even though it should have been installed when installing OpenJDK with conda. This will result in an error mentionning "java.dll" and suggesting to check the `JAVA_HOME` environment variable.

The only fix I could find is to install Java system-wide. You can grab a (free) installer on [Adoptium](https://adoptium.net/en-GB/temurin/releases/?version=17), choosing JRE 17.X for your platform.  
During the installation :

+ choose to install "just for you",
+ enable "Modify PATH variable" as well as "Set or override JAVA_HOME" variable.

Restart the terminal and try again. Now, ImageJ should use the system-wide Java and it should work.

## ABBA QuPath extension
To import registered regions in your QuPath project and be able to convert objects' coordinates in atlas space, the ABBA QuPath extension is required.

1. In QuPath, head to `Edit > Preferences`. In the `Extension` tab, set your `QuPath user directory` to a local directory (usually `C:\Users\USERNAME\QuPath\v0.X.Y`).
2. Create a folder named `extensions` in your QuPath user directory.
2. Download the latest ABBA extension for QuPath from [GitHub](https://github.com/BIOP/qupath-extension-abba/releases) (choose the file `qupath-extension-abba-x.y.z.zip`).
3. Uncompress the archive and copy all .jar files into the `extensions` folder in your QuPath user directory.
4. Restart QuPath. Now, in `Extensions`, you should have an `ABBA` entry.