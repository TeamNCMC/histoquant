/**
 * renameAnnotationsMeasurement.groovy
 *
 * Rename annotations' measurement, selected by name.
 */

def measurementName = 'Length: Fibers: EGFP aera µm^2'
def newName = 'Fibers: EGFP aera µm^2'

// Get objects of interest
def regions = getAnnotationObjects()
    .findAll { it.getROI().isArea() }  // get brain regions
// Loop, get value, remove, and add back
for (region in regions) {
    value = region.measurements.get(measurementName)
    region.measurements.remove(measurementName)
    region.measurements.put(newName, value)
}
