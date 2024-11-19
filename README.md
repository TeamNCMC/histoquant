# histoquant

Python package for histological quantification.

Documentation : [https://teamncmc.github.io/histoquant](https://teamncmc.github.io/histoquant)

## Install
Steps 1-3 below need to be performed only once. If Anaconda is already installed, skip steps 1-2 and use the Anaconda prompt (Powershell) instead.
1. Install [miniconda3](https://docs.anaconda.com/free/miniconda/#id2), as user, add conda to PATH and make it the default interpreter.
2. Open a terminal (PowerShell in Windows). run : `conda init` and restart the terminal.
3. Create a virtual environment named "hq" with Python 3.12 and PyTables:
    ```
    conda create -n hq -c conda-forge python=3.12 pytables
    ```
4. Activate the environment:
    ```
    conda activate hq
    ```
5. Download the repository and unzip it on your computer, or clone with `git`.
5. Browse to the repository from the terminal and install the `histoquant` package:
    ```
    cd /path/to/the/repo
    pip install .
    ```

For more complete installation instruction, see the [documentation](https://teamncmc.github.io/histoquant/main-getting-started.html#slow-start).

## Using notebooks
Some Jupyter notebooks are available in the "docs/demo_notebooks" folder. You can open them in an IDE (such as [vscode](https://code.visualstudio.com/), select the "hq" environment as kernel in the top right) or in the Jupyter web interface (`jupyter notebook` in the terminal, with the "hq" environment activated).

## Brain structures
You can generate brain structures outlines coordinates in three projections (coronal, sagittal, top-view) with the script in scripts/atlas/generate_atlas_outline.py. They are used to overlay brain regions outlines in 2D projection density maps. It might take a while so you can also grab a copy of those files here:
+ allen mouse 10µm : https://arcus.neuropsi.cnrs.fr/s/TYX95k4QsBSbxD5
+ allen cord 20um : https://arcus.neuropsi.cnrs.fr/s/EoAfMkESzJZG74Q

## Build the doc
To build and look at the documentation offline :
In [step 5. above](#install), replace the `pip install .` command with :
```bash
pip install .[doc]
```
Then, run :
```
mkdocs serve
```
Head to [http://localhost:8000/](http://localhost:8000/) from a web browser.
The documentation is built with [MkDocs](https://www.mkdocs.org/) using the [Material theme](https://squidfunk.github.io/mkdocs-material/). [KaTeX](https://katex.org/) CSS and fonts are embedded instead of using a CDN, and are under a [MIT license](https://opensource.org/license/MIT).

## Credits
`histoquant` has been primarly developped by [Guillaume Le Goc](https://legoc.fr) in [Julien Bouvier's lab](https://www.bouvier-lab.com/) at [NeuroPSI](https://neuropsi.cnrs.fr/).