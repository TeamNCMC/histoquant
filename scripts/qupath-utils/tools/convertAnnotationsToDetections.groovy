/**
 * convertAnnotationsToDetections.groovy
 *
 * Convert all annotations whose class correspondond to the specified one to detections,
 * with the same classification.
 */

// Define what class to convert
classToConvert = 'Fibers'

// Find annotations to convert
def annotations = getAnnotationObjects().findAll { it.getPathClass().toString() == classToConvert }
// Uncomment below to get all annotation that CONTAINS the class name -- use with caution
//def annotations = getAnnotationObjects().findAll{it.getPathClass().toString().contains(classToConvert)}

// Create new detections
def newDetections = annotations.collect {
    return PathObjects.createDetectionObject(it.getROI(), it.getPathClass())
}

// Remove annotations
removeObjects(annotations, true)

// Add detections
addObjects(newDetections)

// Insert in hierarchy
insertObjects(getDetectionObjects())
