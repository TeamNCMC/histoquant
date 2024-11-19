/**
 * addAtlasCoordinates.groovy
 *
 * Convert detections centroids coordinates to atlas coordinates in µm,
 * and add them as measurements. It requires the ABBA extension, and registration
 * exported to the QuPath project.
 * Measurements names : "Altas_X", "Altas_Y", "Atlas_Z".
 */

def pixelToAtlasTransform =
    AtlasTools
    .getAtlasToPixelTransform(getCurrentImageData())
    .inverse() // pixel to atlas = inverse of atlas to pixel

getDetectionObjects().forEach(detection -> {
    RealPoint atlasCoordinates = new RealPoint(3)
    MeasurementList ml = detection.getMeasurementList()
    atlasCoordinates.setPosition([detection.getROI().getCentroidX(), detection.getROI().getCentroidY(), 0] as double[])
    pixelToAtlasTransform.apply(atlasCoordinates, atlasCoordinates)
    ml.put('Atlas_X', atlasCoordinates.getDoublePosition(0))
    ml.put('Atlas_Y', atlasCoordinates.getDoublePosition(1))
    ml.put('Atlas_Z', atlasCoordinates.getDoublePosition(2))
})

import net.imglib2.RealPoint
import qupath.lib.measurements.MeasurementList
import qupath.ext.biop.abba.AtlasTools
