/**
 * convertDetectionsToAnnotations.groovy
 *
 * Convert all detections whose class correspondond to the specified one to annotations,
 * with the same classification.
 */

// Define what class to convert
classToConvert = 'V2a cells: AS+'

// Find detections to convert
def detections = getDetectionObjects().findAll { it.getPathClass().toString() == classToConvert }
// Uncomment below to get all annotation that CONTAINS the class name -- use with caution
//def annotations = getDetectionObjects().findAll{it.getPathClass().toString().contains(classToConvert)}

def newAnnotations = detections.collect {
    return PathObjects.createAnnotationObject(it.getROI(), it.getPathClass())
}
// Remove detections
removeObjects(detections, true)

// Add annotations
addObjects(newAnnotations)

// Insert in hierarchy
insertObjects(getDetectionObjects())
