/**
 * stardistDetectionFilters.groovy
 *
 * Detect objects with the stardist extension. Additionally filter out detected objects,
 * based on size, shape and intensity in diffrent compartments and channels.
 * It is based on the stardist extension detection script, here is the original docstring :
 * 
 * This script provides a general template for cell detection using StarDist in QuPath.
 * This example assumes you have fluorescence image, which has a channel called 'DAPI'
 * showing nuclei.
 *
 * If you use this in published work, please remember to cite *both*:
 *  - the original StarDist paper (https://doi.org/10.48550/arXiv.1806.03535)
 *  - the original QuPath paper (https://doi.org/10.1038/s41598-017-17204-5)
 *
 * There are lots of options to customize the detection - this script shows some
 * of the main ones. Check out other scripts and the QuPath docs for more info.
 */

// --- Parameters
def cellClassification = 'Cells: marker-'
def detectionChannel = 'DsRed'  // channel used for detection
def detectionCompartment = 'Nucleus'  // cell compartment to use for measurement, not used if cellExpansion is 0
def validationChannel = 'CFP'  // channel used to exclude cells that are below a threshold
def validationCompartment = 'Cell'  // cell compartment to use for measurement, not used if cellExpansion is 0
def cellExpansion = 0  // cell expansion from detected object. 0 to disable.
def removeBadCells = false  // whether to delete the exluded cells or keep them for inspection (classified as "bad")
def pixelSize = 1  // resolution to use for the detection, in microns
def percentileMin = 1  // minimum percentile for image normalization
def percentileMax = 99  // maximum percentile for image normalization

// --- Filters
def probabilityThreshold = 0.6  // probability threshold
def detectionMeasurement = "Median"  // metric to use, "Mean" or "Median"
def detectionMinThreshold = 500  // threshold for detection channel
def validationMeasurement = "Mean"  // metric to use, "Mean" or "Median"
def validationMinThreshold = 300  // threshold for validation channel
def areaCompartment = 'Nucleus'  // cell compartment to use for measurement, not used if cellExpansion is 0
def minArea = 50
def maxArea = 750
def minCircularity = 0.35  // min. circularity

def modelPath = 'D:/projects/histo/programs/models/stardist/dsb2018_heavy_augment.pb'

// --- Preparation
if (cellExpansion == 0) {
    measurementDetection = detectionChannel + ': ' + detectionMeasurement
    measurementValidation = validationChannel + ': ' + validationMeasurement
    measurementArea = 'Area µm^2'
} else {
    measurementDetection = detectionChannel + ': ' + detectionCompartment + ': ' + detectionMeasurement
    measurementValidation = validationChannel + ': ' + validationCompartment + ': ' + validationMeasurement
    measurementArea = areaCompartment + ': Area µm^2'
}

// Customize how the StarDist detection should be applied
// Here some reasonable default options are specified
def stardist = StarDist2D
    .builder(modelPath)
    .preprocess(
                StarDist2D.imageNormalizationBuilder()
                .maxDimension(4096)
                .percentiles(percentileMin, percentileMax)
                .build()
            )
    .channels(detectionChannel)            // Extract channel called 'DAPI'
    .tileSize(1024)              // Specify width & height of the tile used for prediction
    .threshold(probabilityThreshold)  // Probability (detection) threshold
    .pixelSize(pixelSize)              // Resolution for detection
    .cellExpansion(cellExpansion)            // Expand nuclei to approximate cell boundaries
    .measureShape()              // Add shape measurements
    .measureIntensity()          // Add cell measurements (in all compartments)
    .includeProbability(true)    // Include prediction probability as measurement
    .classify(cellClassification)           // Automatically assign all created objects as 'cellClassification'
    .doLog()                     // Use this to log a bit more information while running the script
    .build()

// Define which objects will be used as the 'parents' for detection
def pathObjects = QP.getSelectedObjects()

// Run detection for the selected objects
if (pathObjects.isEmpty()) {
    // if no selected object, create a full image annotation
    imageAnnotation = QP.createFullImageAnnotation(true)
    pathObjects = QP.getSelectedObjects()
    removeAnnotationFlag = true
} else {
    removeAnnotationFlag = false
}
def imageData = QP.getCurrentImageData()
stardist.detectObjects(imageData, pathObjects)  // perform detection
stardist.close() // This can help clean up & regain memory

// Filter
def toDelete = getDetectionObjects().findAll {
    it.getPathClass().toString() == cellClassification & (
    (measurement(it, measurementArea) < minArea) ||
    (measurement(it, measurementArea) > maxArea) ||
    (measurement(it, 'Circularity') < minCircularity) ||
    (measurement(it, measurementDetection) < detectionMinThreshold) ||
    (measurement(it, measurementValidation) < validationMinThreshold)
    )}

// Cleanup
if (removeBadCells) {
    println('Removing ' + toDelete.size() + ' cells')
    QP.removeObjects(toDelete, true)
} else
{
    println('Classifying ' + toDelete.size() + " cells as 'bad'")
    toDelete.forEach { it.setPathClass(QP.getPathClass(cellClassification + ' bad')) }
}
if (removeAnnotationFlag) {
    QP.removeObject(imageAnnotation, true)
}

// Insert detections in hierarchy
insertObjects(getDetectionObjects())
fireHierarchyUpdate()

println('Done!')

import qupath.ext.stardist.StarDist2D
import qupath.lib.gui.dialogs.Dialogs
import qupath.lib.scripting.QP