/**
 * convertDetectionsClassification.groovy
 *
 * Convert all detections classifications to a another one.
 */

def classToConvert = 'Cells'
def newClass = 'Cells: marker+'

getDetectionObjects().findAll {
    it.getPathClass().toString() == classToConvert}
    .forEach { it.setPathClass(getPathClass(newClass)) }
