/**
 * addRegionsLength.groovy
 *
 * Add the cumulated lengths (in µm) of fibers-like objects (polylines) in each annotation.
 * Adds it as "Classification Length µm" where "Classification" is the classification name.
 */

// Define what classification(s) need to be measured
def classificationNames = ['Fibers: DsRed', 'Fibers: EGFP']

// Get pixel size for conversion
def pixelSize = getCurrentServer().getPixelCalibration().getAveragedPixelSizeMicrons()

// Loop through detections that are to be exported
for (classificationName in classificationNames) {
    // Get objects of interest
    def regions = getAnnotationObjects()
        .findAll { it.getROI().isArea() }  // get brain regions
    def detections = getDetectionObjects()
        .findAll { it.getPathClass().toString() == classificationName }  // get selected detection type
    def detectionsUnion = RoiTools.union(detections.collect { it.getROI() })  // create a ROI combining all detections

    for (region in regions) {
        def regionROI = region.getROI() // get region ROI
        def length = RoiTools.intersection(detectionsUnion, regionROI).getLength()  // compute total length
        def length_um = length * pixelSize  // convert to microns
        region.measurements.put(classificationName + ' Length µm', length_um)
    }
}
