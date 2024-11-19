# Using notebooks
A Jupyter notebook is a way to use Python in an interactive manner. It uses cells that contain Python code, and that are to be executed to immediately see the output, including figures.

You can see some rendered notebooks in the examples here, but you can also download them (downward arrow button on the top right corner of each notebook) and run them locally with your own data.

To do so, you can either use an integrated development environment (basically a supercharged text editor) that supports Jupyter notebooks, or directly the Jupyter web interface.

=== "IDE"
    You can use for instance [Visual Studio Code](https://code.visualstudio.com/), also known as vscode.

    1. Download it and install it.
    2. Launch vscode.
    3. Follow or skip tutorials.
    4. In the left panel, open Extension (squared pieces).
    5. Install the "Python" and "Jupyter" extensions (by Microsoft).
    6. You now should be able to open .ipynb (notebooks) files with vscode. On the top right, you should be able to Select kernel : choose "hq".
=== "Jupyter web interface"
    1. Create a folder dedicated to working with notebooks, for example "Documents\notebooks".
    2. Copy the notebooks you're interested in in this folder.
    3. Open a terminal *inside* this folder (by either using `cd Documents\notebooks` or, in the file explorer in your "notebooks" folder, ++shift+right-button++ to "Open PowerShell window here")
    4. Activate the conda environment :
    ```bash
    conda activate hq
    ```
    5. Launch the Jupyter Lab web interface :
    ```bash
    jupyter lab
    ```
    This should open a web page where you can open the ipynb files.