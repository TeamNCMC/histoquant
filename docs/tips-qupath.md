# QuPath

## Custom scripts
While QuPath graphical user interface (GUI) should meet a lot of your needs, it is very convenient to use [scripting](https://qupath.readthedocs.io/en/stable/docs/scripting/index.html) to automate certain tasks, execute them in batch (on all your images) and do things you couldn't do otherwise. QuPath uses the Groovy programming language, which is mostly Java.

!!! warning inline end
    Not all commands will appear in the history.
In QuPath, in the left panel in the "Workflow" tab, there is an history of most of the commands you used during the session. On the bottom, you can click on `Create workflow` to select the relevant commands and create a script. This will open the built-in script editor that will contain the groovy version of what you did graphically.

!!! tip
    The `scripts/qupath-utils` folder contains a bunch of utility scripts.

They can be run in batch with the three-dotted menu on the bottom right corner of the script editor : `Run for project`, then choose the images you want the script to run on.