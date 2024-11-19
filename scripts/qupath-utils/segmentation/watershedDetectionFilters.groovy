/**
 * watershedDetectionFilters.groovy
 *
 * Perform nucleus detection, cell expansion and measurement, with the built-in
 * cell detection algorithm (enhanced watershed).
 * You can first use the GUI to do this (Analyze > Cell detection > Cell detection)
 * to tune the parameters, then report them here.
 * Remember to check how the cell detection performed before further processing !
 *
 * !!! WARNING !!! Existing detections are cleared : those are lost forever.
 */

// !!! WARNING !!!
// Executing this script will clear all detections in the image !
//clearDetections()

// --- Parameters ---
// -- Cell nomenclature
cellClassification = 'Cells: marker-'

// -- Cell detection parameters
// Here we define the parameters of cell detection. Basically,
// we"ll use the GUI to do this and find the parameters that works best for different images.
// Then, we report here the values used.

// Setup parameters
def detectionChannel = 'EGFP'  // channel used for detection
def validationChannel = 'CFP'  // channel used to exclude cells that are below a threshold
def validationThreshold = 300  // threshold for validation
def validationCompartment = 'Cell' // where to do the measure : Cytoplasm, Cell or Nucleus
def removeBadCells = true  // whether to delete the exluded cells or keep them for inspection (classified as "bad")
def requestedPixelSize = 0.5

// Nucleus parameters
def backgroundRadius = 8
def backgroundByReconstruction = true
def medianFilterRadius = 0
def sigma = 1.5
def minimumArea = 10
def maximumArea = 500

// Intensity parameters
def threshold = 500
def splitByShape = true

// Cell parameters
def cellExpansion = 5
def includeNuclei = true

// General parameters
def smoothBoundaries = true
def makeMeasurements = true

// --- Preparation ---
// -- Create an annotation that covers the whole image
def imageAnnotation = createFullImageAnnotation(true)

// -- Define the parameters in json format for the plugin
def parameters = '{' +
"\"detectionImage\":\"${detectionChannel}\"," +
"\"requestedPixelSizeMicrons\":${requestedPixelSize}," +
"\"backgroundRadiusMicrons\":${backgroundRadius}," +
"\"backgroundByReconstruction\":${backgroundByReconstruction}," +
"\"medianRadiusMicrons\":${medianFilterRadius}," +
"\"sigmaMicrons\":${sigma}," +
"\"minAreaMicrons\":${minimumArea}," +
"\"maxAreaMicrons\":${maximumArea}," +
"\"threshold\":${threshold}," +
"\"watershedPostProcess\":${splitByShape}," +
"\"cellExpansionMicrons\":${cellExpansion}," +
"\"includeNuclei\":${includeNuclei}," +
"\"smoothBoundaries\":${smoothBoundaries}," +
"\"makeMeasurements\":${makeMeasurements}" +
'}'

// --- Processing ---
// Just run the plugin that does the magic
selectObjects(imageAnnotation)  // select the parent Annotation so that the cell detection is ran on it
runPlugin('qupath.imagej.detect.cells.WatershedCellDetection', parameters)

// Get all detections and set their Classification
getDetectionObjects().forEach { it.setPathClass(getPathClass(cellClassification)) }

// Filter out cells that have their cytoplasm fluo. value below the validationThreshold
def allCells = getDetectionObjects().findAll {
    it.getPathClass().toString() == cellClassification }
print(' Found ' + allCells.size() + ' cells.')
println('Filtering...')
def toDelete = getDetectionObjects().findAll {
    it.getPathClass().toString() == cellClassification & (
            (QP.measurement(it, validationCompartment + ': ' + validationChannel + ' mean') < validationThreshold)
    )
}

print(' Removing ' + toDelete.size() + ' cells.')
// Cleanup
if (removeBadCells) {
    QP.removeObjects(toDelete, true)
} else
{
    toDelete.forEach { it.setPathClass(QP.getPathClass(cellClassification + ' bad')) }
}
QP.removeObject(imageAnnotation, true)


// Insert detections in hierarchy
insertObjects(getDetectionObjects())
fireHierarchyUpdate()