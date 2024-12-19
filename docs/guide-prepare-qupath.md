# Prepare QuPath data

`cuisto` uses some QuPath classifications concepts, make sure to be familiar with them with the [official documentation](https://qupath.readthedocs.io/en/stable/docs/concepts/classifications.html#classifications-derived-classifications). Notably, we use the concept of primary classification and derived classification : an object classfied as `First: second` is of classification `First` and of derived classification `second`.

## QuPath requirements
`cuisto` assumes a specific way of storing regions and objects information in the TSV files exported from QuPath. Note that only one primary classification is supported, but you can have any number of derived classifications.

### Detections
Detections are the objects of interest. Their information must respect the following :

+ Atlas coordinates should be in millimetres (mm) and stored as `Atlas_X`, `Atlas_Y`, `Atlas_Z`. They correspond, respectively, to the anterio-posterior (rostro-caudal) axis, the inferio-superior (dorso-ventral) axis and the left-right (medio-lateral) axis.
+ They must have a derived classification, in the form `Primary: second`. Primary would be an object type (cells, fibers, ...), the second one would be a biological marker or a detection channel (fluorescence channel name), for instance : `Cells: some marker`, or `Fibers: EGFP`.
+ The classification must match exactly the corresponding measurement in the annotations (see below).

### Annotations
Annotations correspond to the atlas regions. Their information must respect the following :

+ They should be imported with the ABBA extension as acronyms and splitting left/right. Therefore, the annotation name should be the region acronym and its classification should be formatted as `Hemisphere: acronym` (for ex. `Left: PAG`).
+ Measurements names should be formatted as :  
`Primary classification: derived classification measurement name`.  
For instance :  
    + if one has *cells* with *some marker* and *count* them in each atlas regions, the measurement name would be :  
    `Cells: some marker Count`.
    + if one segments *fibers* revealed in the *EGFP* channel and measures the cumulated *length* in µm in each atlas regions, the measurement name would be :  
`Fibers: EGFP Length µm`.
+ Any number of markers or channels are supported.

## Measurements

### Metrics supported by `cuisto`
While you're free to add any measurements as long as they follow [the requirements](#qupath-requirements), keep in mind that for atlas regions quantification, `cuisto` will only compute, pool and average the following metrics :

- the base measurement itself
    - if "µm" is contained in the measurement name, it will also be converted to mm (\(\div\)1000)
- the base measurement divided by the region area in µm² (density in something/µm²)
- the base measurement divided by the region area in mm² (density in something/mm²)
- the squared base measurement divided by the region area in µm² (could be an index, in weird units...)
- the relative base measurement : the base measurement divided by the total base measurement across all regions *in each hemisphere*
- the relative density : density divided by total density across all regions *in each hemisphere*

It is then up to you to select which metrics among those to compute and display and name them, via the [configuration file](main-configuration-files.md#configtoml).

For punctal detections (eg. objects whose only the centroid is considered), only the atlas coordinates are used, to compute and display spatial distributions of objects across the brain (using their classifications to give each distributions different hues).  
For fibers-like objects, it requires to export the lines detections atlas coordinates as JSON files, with the `exportFibersAtlasCoordinates.groovy` script (this is done automatically when using the [pipeline](guide-pipeline.md)).

### Adding measurements
#### Count for cell-like objects
The groovy script under `scripts/qupath-utils/measurements/addRegionsCount.groovy` will add a properly formatted count of objects of selected classifications in all atlas regions. This is used for punctual objects (polygons or points), for example objects created in QuPath or with the [segmentation script](api-script-segment.md).

#### Cumulated length for fibers-like objects
The groovy script under `scripts/qupath-utils/measurements/addRegionsLength.groovy` will add the properly formatted cumulated lenghth in microns of fibers-like objects in all atlas regions. This is used for polylines objects, for example generated with the [segmentation script](api-script-segment.md).

#### Custom measurements
Keeping in mind [`cuisto` limitations](#metrics-supported-by-cuisto), you can add any measurements you'd like.

For example, you can run a [pixel classifier](https://qupath.readthedocs.io/en/stable/docs/tutorials/pixel_classification.html) in all annotations (eg. atlas regions). Using the `Measure` button, it will add a measurement of [the area covered by classified pixels](https://qupath.readthedocs.io/en/stable/docs/tutorials/measuring_areas.html#generating-results). Then, you can use the script located under `scripts/qupath-utils/measurements/renameMeasurements.groovy` to rename the generated measurements with a [properly-formatted name](#annotations). Finally, you can [export](#qupath-export) regions measurements.

Since `cuisto` will compute a "density", eg. the measurement divided by the region area, in this case, it will correspond to the fraction of surface occupied by classified pixels. This is showcased in the [Examples](demo_notebooks/fibers_coverage.ipynb).

## QuPath export
Once you imported atlas regions registered with ABBA, detected objects in your images and added [properly formatted](#qupath-requirements) measurements to detections and annotations, you can : 

+ Head to `Measure > Export measurements`
+ Select relevant images
+ Choose the `Output file` (specify in the file name if it is a detections or annotations file)
+ Chose either `Detections` or `Annoations` in `Export type`
+ Click `Export`

Do this for both Detections and Annotations, you can then use those files with `cuisto` (see the [Examples](main-using-notebooks.md)).

