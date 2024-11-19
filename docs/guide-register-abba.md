# Registration with ABBA

The [ABBA documentation](https://abba-documentation.readthedocs.io/en/latest/) is quite extensive and contains guided tutorials and a video tutorial. You should therefore check it out ! Nevertheless, you will find below some quick reminders.

## Import a QuPath project
Always use ABBA with a QuPath project, if you import the images directly it will not be possible to export the results back to QuPath. In the toolbar, head to `Import > Import QuPath Project`.

+ Select the .qproj file corresponding to the QuPath project to be aligned.
+ Initial axis position : this is the initial position where to put your stack. It will be modified afterwards.
+ Axis increment between slices : this is the spatial spacing, in mm, between two slices. This would correspond to the slice thickness multiplied by the number of set. If your images are ordered from rostral to caudal, set it negative.

!!! warning
    ABBA is not the most stable software, it is highly recommended to [save](#abba-state-file) in a different file each time you do anything.

## Navigation

### Interface
+ ++left-button++ + drag to select slices
+ ++right-button++ for display options
+ ++right-button++ + drag to browse the view
+ ++middle-button++ to zoom in and or out

### Right panel
In the right panel, there is everything related to the images, both yours and the atlas.

In the `Atlas Display` section, you can turn on and off different channels (the first is the reference image, the last is the regions outlines).
The `Displayed slicing [atlas steps]` slider can increase or decrease the number of *displayed* 2D slices extracted from the 3D volume. It is comfortable to set to to the same spacing as your slices. Remember it is in "altas steps", so for an atlas imaged at 10µm, a 120µm spacing corresponds to 12 atlas steps.

The `Slices Display` section lists all your slices. ++ctrl+a++ to select all, and click on the `Vis.` header to make them visible. Then, you can turn on and off each channels (generally the NISSL channel and the ChAT channel will be used) by clicking on the corresponding header. Finally, set the display limits clicking on the empty header containing the colors.

++right-button++ in the main view to `Change overlap mode` twice to get the slices right under the atlas slices.

!!! tip
    Every action in ABBA are stored and are cancellable with ++right-button+z++, **except** the [Interactive transform](#coarse-linear-manual-deformation).

## Find position and angle
This is the hardest task. You need to drag the slices along the rostro-caudal axis and modify the virtual slicing angle (`X Rotation [deg]` and `Y Rotation [deg]` sliders at the bottom of the right panel) until you match the brain structures observed in both your images and the atlas.

!!! tip
    With a high number of slices, most likely, it will be impossible to find a position and slicing angle that works for all your slices. In that case, you should procede in batch, eg. sub-stack of images with a unique position and slicing angle that works for all images in the sub-stack. Then, remove the remaining slices (select them, ++right-button++ `> Remove Selected Slices`), but **do not** remove them from the QuPath project.

    Procede as usual, including [saving](#abba-state-file) (note the slices range it corresponds to) and [exporting](#export-registration-back-to-qupath) the registration back to QuPath. Then, reimport the project in a fresh ABBA instance, remove the slices that were already registered and redo the whole process with the next sub-stack and so on.

Once you found the correct position and slicing angle, it **must not change** anymore, otherwise the registration operations you perform will not make any sense anymore.

## In-plane registration
The next step is to deform your slices to match the corresponding atlas image, extracted from the 3D volume given the position and virtual slicing angle defined at the previous step.

!!! info
    ABBA makes the choice to deform *your* slices to the atlas, but the transformations are invertible. This means that you will still be able to work on your raw data and deform the altas onto it instead.

In image processing, there are two kinds of deformation one can apply on an image :

+ Affine (or linear) : simple, image-wide, linear operations - translation, rotation, scaling, shearing.
+ Spline (or non-linear) : complex non-linear operations that can allow for local deformation.

Both can be applied manually or automatically (if the imaging quality allows it).
You have different tools to achieve this, all of which can be combined in any order, **except** the Interactive transform tool (coarse, linear manual deformation).

Change the overlap mode (++right-button++) to overlay the slice onto the atlas regions borders. Select the slice you want to align.

### Coarse, linear manual deformation
While not mandatory, if this tool shall be used, it must be before any operation as it is not cancellable.
Head to `Register > Affine > Interactive transform`.  
This will open a box where you can rotate, translate and resize the image to make a first, coarse alignment.

Close the box. Again, this is not cancellable. Afterwards, you're free to apply any numbers of transformations in any order.

### Automatic registration
This uses the [elastix](https://elastix.dev) toolbox to compute the transformations needed to best match two images. It is available in both affine and spline mode, in the `Register > Affine` and `Register > Spline` menus respectively.

In both cases, it will open a dialog where you need to choose :

+ Atlas channels : the reference image of the atlas, usually channel number 0
+ Slices channels : the fluorescence channel that looks like the most to the reference image, usually channel number 0
+ Registration re-sampling (micrometers) : the pixel size to resize the images before registration, as it is a computationally intensive task. Going below 20µm won't help much.

For the Spline mode, there an additional parameter :

+ Number of control points along X : the algorithm will set points as a grid in the image and perform the transformations from those. The higher number of points, the more local transformations will be.

### Manual registration
This uses [BigWarp](https://imagej.net/plugins/bigwarp) to manually deform the images with the mouse. It can be done from scratch (eg. you place the points yourself) or from a previous registration (either a previous BigWarp session or elastix in Spline mode).

#### From scratch
`Register > Spline > BigWarp registration` to launch the tool. Choose the atlas that allows you to best see the brain structures (usually the regions outlines channels, the last one), and the reference fluorescence channel.

It will open two viewers, called "**BigWarp moving image**" and "**BigWarp fixed image**". Briefly, they correspond to the two spaces you're working in, the "Atlas space" and the "Slice space".

!!! tip
    Do not panick yet, while the explanations might be confusing (at least they were to me), in practice, it is easy, intuitive and can even be fun (sometimes, at small dose).

To browse the viewer, use ++right-button++ + drag (++left-button++ is used to rotate the viewer), ++middle-button++ zooms in and out.

The idea is to place points, called landmarks, that *always* **go in pairs** : one in the moving image and one where it corresponds to in the fixed image (or vice-versa). In practice, we will only work in the **BigWarp fixed image** viewer to place landmarks in both space in one click, then drag it to the corresponding location, with a live feedback of the transformation needed to go from one to another.

To do so :

1. Press ++space++ to switch to the "Landmark mode".

    !!! warning
        In "Landmark mode", ++right-button++ can't be used to browse the view anymore. To do so, turn off the "Landmark mode" hitting ++space++ again. 

2. Use ++ctrl+left-button++ to place a landmark.

    !!! info
        At least 4 landmarks are needed before activating the live-transform view.

3. When there are at least 4 landmarks, hit ++t++ to activate the "Transformed" view. `Transformed` will be written at the bottom.
4. Hold ++left-button++ on a landmark to drag it to deform the image onto the atlas.
5. Add as many landmarks as needed, when you're done, find the Fiji window called "Big Warp registration" that opened at the beginning and click `OK`.

!!! tip "Important remarks and tips"
    + A landmark is a location where you said "this location correspond to this one". Therefore, BigWarp is not allowed to move this particular location. Everywhere else, it is free to transform the image without any restrictions, including the borders. Thus, it is a good idea to **delimit the coarse contour of the brain with landmarks** to constrain the registration.
    + ++left-button++ without holding ++ctrl++ will place a landmark in the fixed image only, without pair, and BigWarp won't like it. To **delete landmarks**, head to the "Landmarks" window that lists all of them. They highlight in the viewer upon selection. Hit ++del++ to delete one. Alternatively, click on it on the viewer and hit ++del++.

#### From a previous registration
Head to `Register > Edit last Registration` to work on a previous registration.

If the previous registration was done with elastix (Spline) or BigWarp, it will launch the BigWarp interface exactly like above, but with landmarks already placed, either on a grid (elastix) or the one you manually placed (BigWarp).

!!! tip
    It will ask which channels to use, you can modify the channel for your slices to work on two channels successively. For instance, one could make a first registration using the NISSL staining, then refine the motoneurons with the ChAT staining, if available.

## ABBA state file
ABBA can save the state you're in, from the `File > Save State` menu. It will be saved as a `.abba` file, which is actually a zip archive containing a bunch of [JSON](tips-formats.md#json-and-geojson-files), listing every actions you made and in *which order*, meaning you will stil be able to cancel actions after quitting ABBA.

To load a state, quit ABBA, launch it again, then choose `File > Load State` and select the `.abba` file to carry on with the registration.

!!! danger "Save, save, save !"
    Those state files are cheap, eg. they are lightweight (less than 200KB). You should save the state each time you finish a slice, and you can keep all your files, without overwritting the previous ones, appending a number to its file name. This will allow to roll back to the previous slice in the event of any problem you might face.

## Export registration back to QuPath

### Export the registration from ABBA
Once you are satisfied with your registration, select the registered slices and head to `Export > QuPath > Export Registrations To QuPath Project`. Check the box to make sure to get the latest registered regions.

It will export several files in the QuPath projects, including the transformed atlas regions ready to be imported in QuPath and the transformations parameters to be able to convert coordinates from the extension.

### Import the registration in QuPath
Make sure you installed the [ABBA extension](guide-install-abba.md#abba-qupath-extension) in QuPath.


From your project with an image open, the basic usage is to head to `Extensions > ABBA > Load Atlas Annotations into Open Image`.
Choose to `Split Left and Right Regions` to make the two hemispheres independent, and choose the "acronym" to name the regions. The registered regions should be imported as Annotations in the image.

!!! tip
    With ABBA in regular Fiji using the CCFv3 Allen mouse brain atlas, the left and right regions are flipped, because ABBA considers the slices as backward facing. The `importAbba.groovy` script located in `scripts/qupath-utils-atlas` allows you to flip left/right regions names. This is OK because the Allen brain is symmetrical by construction.

For more complex use, check the Groovy scripts in `scripts/qupath-utils/atlas`. ABBA registration is used throughout the guides, to either work with brain regions (and count objects for instance) or to get the detections' coordinates in the atlas space.