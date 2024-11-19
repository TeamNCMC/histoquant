# Detect objects with QuPath

The [QuPath documentation](https://qupath.readthedocs.io/en/stable/) is quite extensive, detailed, very well explained and contains full guides on how to create a QuPath project and how to find objects of interests. It is therefore a highly recommended read, nevertheless, you will find below some quick reminders.

## QuPath project
QuPath works with [projects](https://qupath.readthedocs.io/en/stable/docs/tutorials/projects.html). It is basically a folder with a main `project.qproj` file, which is a [JSON](tips-formats.md#json-and-geojson-files) file that contains all the data about your images *except* the images themselves. Algonside, there is a `data` folder with an entry for each image, that stores the thumbnails, metadata about the image and detections and annotations *but*, again, *not* the image itself. The actual images can be stored anywhere (including a remote server), the QuPath project merely contains the information needed to fetch them and display them. QuPath will *never* modify your image data.

This design makes the QuPath project itself lightweight (should never exceed 500MB even with millions of detections), and portable : upon opening, if QuPath is not able to find the images where they should be, it will ask for their new locations.

!!! tip
    It is recommended to create the QuPath project locally on your computer, to avoid any risk of conflicts if two people open it at the same time. Nevertheless, you should backup the project regularly on a remote server.

To create a new project, simply drag & drop an empty folder into QuPath window and accept to create a new empty project. Then, add images :

+ If you have a single file, just drag & drop it in the main window.
+ If you have several images, in the left panel, click `Add images`, then `Choose files` on the bottom. Drag & drop does not really work as the images will not be sorted properly.

Then, choose the following options :

`Image server`

: Default (let QuPath decide)

`Set image type`

: Most likely, fluorescence

`Rotate image`

: No rotation (unless all your images should be rotated)

`Optional args`

: Leave empty

`Auto-generate pyramids`

: Uncheck

`Import objects`

: Uncheck

`Show image selector`

: Might be useful to check if the images are read correctly (mostly for CZI files).

## Detect objects
### Built-in cell detection

QuPath has a built-in cell detection feature, available in `Analyze > Cell detection`. You hava a full tutorial in the [official documentation](https://qupath.readthedocs.io/en/stable/docs/tutorials/cell_detection.html).

Briefly, this uses a watershed algorithm to find bright spots and can perform a cell expansion to estimate the full cell shape based on the detected nuclei. Therefore, this works best to segment nuclei but one can expect good performance for cells as well, depending on the imaging and staining conditions.

!!! tip
    In `scripts/qupath-utils/segmentation`, there is `watershedDetectionFilters.groovy` which uses this feature from a script. It further allows you to filter out detected cells based on shape measurements as well as fluorescence itensity in several channels and cell compartments.

### Pixel classifier
Another very powerful and versatile way to segment cells if through machine learning. Note the term "machine" and not "deep" as it relies on statistics theory from the 1980s. QuPath provides an user-friendly interface to that, similar to what [ilastik](https://www.ilastik.org/) provides.

The general idea is to train a model to classify every pixel as a signal or as background. You can find good resources on how to procede in the [official documentation](https://qupath.readthedocs.io/en/stable/docs/tutorials/pixel_classification.html) and some additionnal tips and tutorials on Michael Neslon's blog ([here](https://www.imagescientist.com/mpx-pixelclassifier) and [here](https://www.imagescientist.com/brightfield-4-pixel-classifier)).

Specifically, you will manually annotate some pixels of objects of interest and background. Then, you will apply some image processing filters (gaussian blur, laplacian...) to reveal specific features in your images (shapes, textures...). Finally, the pixel classifier will fit a model on those pixel values, so that it will be able to predict if a pixel, given the values with the different filters you applied, belongs to an object of interest or to the background.

This is done in an intuitive GUI with live predictions to get an instant feedback on the effects of the filters and manual annotations.

#### Train a model
First and foremost, you should use a QuPath project dedicated to the training of a pixel classifier, as it is the only way to be able to edit it later on.

1. You should choose some images from different animals, with different imaging conditions (staining efficiency and LED intensity) in different regions (eg. with different objects' shape, size, sparsity...). The goal is to get the most diversity of objects you could encounter in your experiments. 10 images is more than enough !
2. Import those images to the new, dedicated QuPath project.
3. Create the classifications you'll need, "Cells: marker+" for example. The "Ignore*" classification is used for the background.
4. Head to `Classify > Pixel classification > Train pixel classifier`, and turn on `Live prediction`.
5. Load all your images in `Load training`.
6. In `Advanced settings`, check `Reweight samples` to help make sure a classification is not over-represented.
7. Modify the different parameters :
    + `Classifier` : typically, `RTrees` or `ANN_MLP`. This can be changed dynamically afterwards to see which works best for you.
    + `Resolution` : this is the pixel size used. This is a trade-off between accuracy and speed. If your objects are only composed of a few pixels, you'll the full resolution, for big objects reducing the resolution will be faster.
    + `Features` : this is the core of the process -- where you choose the filters. In `Edit`, you'll need to choose :
        - The fluorescence channels
        - The scales, eg. the size of the filters applied to the image. The bigger, the coarser the filter is. Again, this will depend on the size of the objects you want to segment.
        - The features themselves, eg. the filters applied to your images before feeding the pixel values to the model. For starters, you can select them all to see what they look like.
    + `Output` :
        - `Classification` : QuPath will directly classify the pixels. Use that to [create objects directly from the pixel classifier](#built-in-create-objects) within QuPath.
        - `Probability` : this will output an image where each pixel is its probability to belong to each of the classifications. This is useful to [create objects externally](#probability-map-segmentation).
8. In the bottom-right corner of the pixel classifier window, you can select to display each filters individually. Then in the QuPath main window, hitting ++c++ will switch the view to appreciate what the filter looks like. Identify the ones that makes your objects the most distinct from the background as possible. Switch back to `Show classification` once you begin to make annotations.
9. Begin to annotate ! Use the Polyline annotation tool (++v++) to classify **some** pixels belonging to an object and **some** pixels belonging to the background across your images.
    
    !!! tip
        You can select the `RTrees` Classifier, then `Edit` : check the `Calculate variable importance` checkbox. Then in the log (++ctrl+shift+l++), you can inspect the weight each features have. This can help discard some filters to keep only the ones most efficient to distinguish the objects of interest.

10. See in live the effect of your annotations on the classification using ++c++ and continue until you're satisfied.

    !!! Important
        This is *machine* learning. The lesser annotations, the better, as this will make your model more general and adapt to new images. The goal is to find the *minimal* number of annotations to make it work.

11. Once you're done, give your classifier a name in the text box in the bottom and save it. It will be stored as a [JSON](tips-formats.md#json-and-geojson-files) file in the `classifiers` folder of the QuPath project. This file can be imported in your other QuPath projects.

#### Built-in create objects
Once you imported your model JSON file (`Classify > Pixel classification > Load pixel classifier`, three-dotted menu and `Import from file`), you can create objects out of it, measure the surface occupied by classified pixels in each annotation or classify existing detections based on the prediction at their centroid.

In `scripts/qupath-utils/segmentation`, there is a `createDetectionsFromPixelClassifier.groovy` script to batch-process your project.

#### Probability map segmentation
Alternatively, a Python script provided with `histoquant` can be used to segment the probability map generated by the pixel classifier (the script is located in `scripts/segmentation`).

You will first need to export those with the `exportPixelClassifierProbabilities.groovy` script (located in `scripts/qupath-utils`).

Then the segmentation script can :

+ find punctal objects as polygons (with a shape) or points (punctal) than can be counted.
+ trace fibers with skeletonization to create lines whose lengths can be measured.

Several parameters have to be specified by the user,  see the segmentation script [API reference](api-script-segment.md). This script will generate [GeoJson](tips-formats.md#json-and-geojson-files) files that can be imported back to QuPath with the `importGeojsonFiles.groovy` script.

### Third-party extensions
QuPath being open-source and extensible, there are third-party extensions that implement popular deep learning segmentation algorithms directly in QuPath. They can be used to find objects of interest as detections in the QuPath project and thus integrate nicely with `histoquant` to quantify them afterwards.

#### InstanSeg
QuPath extension : [https://github.com/qupath/qupath-extension-instanseg](https://github.com/qupath/qupath-extension-instanseg)  
Original repository : [https://github.com/instanseg/instanseg](https://github.com/instanseg/instanseg)  
Reference papers : [doi:10.48550/arXiv.2408.15954](https://doi.org/10.48550/arXiv.2408.15954), [doi:10.1101/2024.09.04.611150](https://doi.org/10.1101/2024.09.04.611150)

#### Stardist
QuPath extension : [https://github.com/qupath/qupath-extension-stardist](https://github.com/qupath/qupath-extension-stardist)  
Original repository : [https://github.com/stardist/stardist](https://github.com/stardist/stardist)  
Reference paper : [doi:10.48550/arXiv.1806.03535](https://doi.org/10.48550/arXiv.1806.03535)

There is a `stardistDetectionFilter.groovy` script in `scripts/qupath-utils/segmentation` to use it from a script which further allows you to filter out detected cells based on shape measurements as well as fluorescence itensity in several channels and cell compartments.

#### Cellpose
QuPath extension : [https://github.com/BIOP/qupath-extension-cellpose](https://github.com/BIOP/qupath-extension-cellpose)  
Original repository : [https://github.com/MouseLand/cellpose](https://github.com/MouseLand/cellpose)  
Reference papers : [doi:10.1038/s41592-020-01018-x](https://doi.org/10.1038/s41592-020-01018-x), [doi:10.1038/s41592-022-01663-4](https://doi.org/10.1038/s41592-022-01663-4), [doi:10.1101/2024.02.10.579780](https://doi.org/10.1101/2024.02.10.579780)

There is a `cellposeDetectionFilter.groovy` script in `scripts/qupath-utils/segmentation` to use it from a script which further allows you to filter out detected cells based on shape measurements as well as fluorescence itensity in several channels and cell compartments.

#### SAM
QuPath extension : [https://github.com/ksugar/qupath-extension-sam](https://github.com/ksugar/qupath-extension-sam)  
Original repositories : [samapi](https://github.com/ksugar/samapi), [SAM](https://github.com/facebookresearch/segment-anything)  
Reference papers : [doi:10.1101/2023.06.13.544786](https://doi.org/10.1101/2023.06.13.544786), [doi:10.48550/arXiv.2304.02643](https://doi.org/10.48550/arXiv.2304.02643)

This is more an interactive annotation tool than a fully automatic segmentation algorithm.