/**
 * addRegionsCount.groovy
 *
 * Add the number of each detections types in each annotation.
 * Adds it as "Classification Count" where "Classification" is the classification name.
 */

// Define what classification(s) need to be counted
def classificationNames = ['Cells: marker+', 'Cells: marker-']

// Loop through detections that are to be exported
for (classificationName in classificationNames) {
    // Get objects of interest
    def regions = getAnnotationObjects()
        .findAll { it.getROI().isArea() }  // get brain regions

    for (region in regions) {
        def count = countDetectionsInAnnotation(region, classificationName)
        region.measurements.put(classificationName + ' Count', count)
    }
}

def countDetectionsInAnnotation(annotation, classification) {
    // Counts detections of classification `classification` in `annotation`.
    return annotation.getChildObjects().findAll {
        (it.getPathClass().toString() == classification) &
        (it.isDetection())
    }.size()
}
