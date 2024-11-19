/**
 * importAbbaWithCoordinates.groovy
 *
 * Import atlas regions as annotations from ABBA, and add atlas coordinates
 * to detections measurements in mm.
 * Optionnaly flip left/right regions names.
 * It requires the ABBA extension, and registration exported to the QuPath project.
 *
 * Warning : it will remove all annotations.
 */

// Flip Left / Right regions names.
def mirrorLeftRight = true

removeObjects(getAnnotationObjects(), true) // last argument = keep child objects ?

def pixelToAtlasTransform =
    AtlasTools
    .getAtlasToPixelTransform(getCurrentImageData())
    .inverse() // pixel to atlas = inverse of atlas to pixel

// Import ABBA regions
AtlasTools.loadWarpedAtlasAnnotations(getCurrentImageData(), 'acronym', true)

// Mirror if required
if (mirrorLeftRight) {
    getAnnotationObjects().forEach {
        if (it.getPathClass() != null) {
            String pc = it.getPathClass()
            if (pc.startsWith('Left: ')) {
                it.setPathClass(getPathClass('Right: ' + it.getName()))
            }
            else if (pc.startsWith('Right'))
                it.setPathClass(getPathClass('Left: ' + it.getName()))
        }
    }
}

// Add detections centroids coordinates
getDetectionObjects().forEach(detection -> {
    RealPoint atlasCoordinates = new RealPoint(3)
    MeasurementList ml = detection.getMeasurementList()
    atlasCoordinates.setPosition([detection.getROI().getCentroidX(), detection.getROI().getCentroidY(), 0] as double[])
    pixelToAtlasTransform.apply(atlasCoordinates, atlasCoordinates)
    ml.putMeasurement('Atlas_X', atlasCoordinates.getDoublePosition(0))
    ml.putMeasurement('Atlas_Y', atlasCoordinates.getDoublePosition(1))
    ml.putMeasurement('Atlas_Z', atlasCoordinates.getDoublePosition(2))
})

// Update hierarchy
insertObjects(getDetectionObjects())
fireHierarchyUpdate()

import net.imglib2.RealPoint
import qupath.lib.measurements.MeasurementList
import qupath.ext.biop.abba.AtlasTools
