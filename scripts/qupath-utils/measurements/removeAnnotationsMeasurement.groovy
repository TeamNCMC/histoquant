/**
 * removeAnnotationsMeasurement.groovy
 *
 * Remove annotations' measurement, selected by name.
 */

measurementName = 'Cells Count'

// Get atlas regions
def regions = getAnnotationObjects().findAll { it.getROI().isArea() }
// Loop and remove
for (region in regions) {
    region.measurements.remove(measurementName)
}
