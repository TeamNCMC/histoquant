/**
 * cellposeDetectionFilters.groovy
 *
 * Detect objects with the Cellpose extension. Additionally filter out detected objects,
 * based on size, shape and intensity in diffrent compartments and channels.
 * It is based on the Cellpose extension detection script, here is the original docstring :
 *
 * Cellpose Detection Template script
 * @author Olivier Burri
 *
 * This script is a template to detect objects using a Cellpose model from within QuPath.
 * After defining the builder, it will:
 * 1. Find all selected annotations in the current open ImageEntry
 * 2. Export the selected annotations to a temp folder that can be specified with tempDirectory()
 * 3. Run the cellpose detction using the defined model name or path
 * 4. Reimport the mask images into QuPath and create the desired objects with the selected statistics
 *
 * NOTE: that this template does not contain all options, but should help get you started
 * See all options in https://biop.github.io/qupath-extension-cellpose/qupath/ext/biop/cellpose/CellposeBuilder.html
 * and in https://cellpose.readthedocs.io/en/latest/command.html
 *
 * NOTE 2: You should change pathObjects get all annotations if you want to run for the project. By default this script
 * will only run on the selected annotations.
 */

// --- Parameters
def cellClassification = 'V2a cells'
def detectionChannel = 'DsRed'  // channel used for detection
def detectionCompartment = 'Nucleus'  // cell compartment to use for measurement, not used if cellExpansion is 0
def validationChannel = 'CFP'  // channel used to exclude cells that are below a threshold
def validationCompartment = 'Cell'  // cell compartment to use for measurement, not used if cellExpansion is 0
def cellExpansion = 0  // cell expansion from detected object. 0 to disable.
def cellDiameter = 30  // median objects diameter, in microns
def pixelSize = 0.4  // resolution to use for the detection, in microns
def percentileMin = 1  // minimum percentile for image normalization
def percentileMax = 99.8  // maximum percentile for image normalization
def removeBadCells = true  // whether to delete the exluded cells or keep them for inspection (classified as "bad")

// --- Filters
def probabilityThreshold = 0.6  // probability threshold
def flowThreshold = 0.4  // flow threshold (default 0.4)
def detectionMeasurement = 'Mean'  // "Mean" or "Median"
def detectionMinThreshold = 2000  // threshold for detection channel
def validationMeasurement = 'Mean'  // "Mean" or "Median"
def validationMinThreshold = 1500  // threshold for validation channel
def areaCompartment = 'Nucleus'  // cell compartment to use for measurement, not used if cellExpansion is 0
def minArea = 80
def maxArea = 500
def minCircularity = 0.5  // min. circularity

def modelPath = 'cyto3'

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

// Customize how the Cellpose detection should be applied
def cellpose = Cellpose2D.builder(modelPath)
        .pixelSize(pixelSize)  // Resolution for detection in um
        .channels(detectionChannel)  // Select detection channel(s)
        .normalizePercentilesGlobal(percentileMin, percentileMax, 10) // Convenience global percentile normalization. arguments are percentileMin, percentileMax, dowsample.
        .tileSize(1024)                  // If your GPU can take it, make larger tiles to process fewer of them. Useful for Omnipose
        .cellprobThreshold(probabilityThreshold)  // Threshold for the mask detection, defaults to 0.0
        .flowThreshold(flowThreshold)  // Threshold for the flows, defaults to 0.4
        .diameter(cellDiameter)  // Median object diameter. Set to 0.0 for the `bact_omni` model or for automatic computation
        .cellExpansion(cellExpansion)  // Approximate cells based upon nucleus expansion
        .classify(cellClassification)  // PathClass to give newly created objects
        .measureShape()  // Add shape measurements
        .measureIntensity()  // Add cell measurements (in all compartments)
        .build()

// Define which objects will be used as the 'parents' for detection
def pathObjects = QP.getSelectedObjects()

// Run detection for the selected objects
if (pathObjects.isEmpty()) {
    // if no selected object, create a full image annotation
    pathObjects = QP.createFullImageAnnotation(true)
    removeAnnotationFlag = true
} else {
    removeAnnotationFlag = false
}
def imageData = QP.getCurrentImageData()
cellpose.detectObjects(imageData, pathObjects)

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
    QP.removeObject(pathObjects, true)
}

println('Done!')

import qupath.ext.biop.cellpose.Cellpose2D
