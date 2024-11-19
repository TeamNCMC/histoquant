/**
 * addAtlasCoordinatesWithStereo.groovy
 *
 * Convert detections centroids coordinates to CCFv3 coordinates in mm,
 * and add them as measurements. Additionnaly, convert those in stereotaxic
 * coordinates (bregma-lambda).
 * It requires the ABBA extension, and registration exported to the QuPath project.
 * CCFv3 measurements names : "Altas_X", "Altas_Y", "Atlas_Z".
 * Stereotaxic measurements names : "AP", "DV", "ML".
 * See :
 * https://forum.image.sc/t/getting-ap-position-bregma-coordinate-from-abba-to-qupath/74500/2
 * https://community.brain-map.org/t/how-to-transform-ccf-x-y-z-coordinates-into-stereotactic-coordinates/1858
 *
 * Note that the sterotaxic conversion is only an empirical approximation.
 */

getDetectionObjects().forEach(detection -> {
    RealPoint atlasCoordinates = new RealPoint(3)
    MeasurementList ml = detection.getMeasurementList()
    atlasCoordinates.setPosition([detection.getROI().getCentroidX(), detection.getROI().getCentroidY(), 0] as double[])
    pixelToAtlasTransform.apply(atlasCoordinates, atlasCoordinates)

    def x_ccfv3 = atlasCoordinates.getDoublePosition(0)
    def y_ccfv3 = atlasCoordinates.getDoublePosition(1)
    def z_ccfv3 = atlasCoordinates.getDoublePosition(2)

    ml.putMeasurement('Atlas_X', x_ccfv3)
    ml.putMeasurement('Atlas_Y', y_ccfv3)
    ml.putMeasurement('Atlas_Z', z_ccfv3)

    // Step 1: center the CCF on Bregma
    def x_stereo = x_ccfv3 - 5.40 //The position is already in millimeter
    def y_stereo = y_ccfv3 - 0.44
    def z_stereo = z_ccfv3 - 5.70

    // Step 2: Rotate the CCF
    def angleCorrection = 5.0 / 180.0 * Math.PI
    def rot_x_stereo = x_stereo * Math.cos(angleCorrection) - y_stereo * Math.sin(angleCorrection)
    def rot_y_stereo = x_stereo * Math.sin(angleCorrection) + y_stereo * Math.cos(angleCorrection)
    x_stereo = rot_x_stereo
    y_stereo = rot_y_stereo

    // Step 3: squeeze the DV axis
    y_stereo = y_stereo * 0.9434

    // Step 4: add measurements
    ml.putMeasurement('AP', x_stereo)
    ml.putMeasurement('DV', y_stereo)
    ml.putMeasurement('ML', z_stereo)
})

import net.imglib2.RealPoint
import qupath.lib.measurements.MeasurementList
import qupath.ext.biop.abba.AtlasTools