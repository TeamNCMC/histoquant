/**
* exportFibersAtlasCoordinates.groovy
*
* export polylines objects atlas coordinates in JSON files.
* Polylines centroids do not make sense, the coordinates of each points composing
* the lines are required. This is huge so CSV format is unfit, JSON is used instead.
*
* Output files will be stored in, relative to the QuPath project parent directory :
* $folderPrefix$segmentation/$segTag$/detections
* where $folderPrefix$ and $segTag$ are defined below.
*
* Assumes the polylines were generated with the `segment_images.py` script, eg.
* detections should have a "Length µm" and a "skeleton_id" measurement. Otherwise,
* comment out those two line in the script :
*   'skeleton_id': detection.getMeasurements()['skeleton_id'],
*   'length_um': detection.getMeasurements()['Length µm'],
*
* ! WARNING ! Existing files will be overwritten.
*/

print('Exporting fibers coordinates...')

// Parameters
def folderPrefix = 'id_'  // output folder name, "segmentation" will be appended
def segTag = 'fibers'  // type of segmentation
def atlas = 'CCFv3'  // stored in the file for reference

// Build file name
def projectParentDir = new File(buildFilePath(PROJECT_BASE_DIR)).getParent()
def baseDir = projectParentDir +
                '/' + folderPrefix + 'segmentation' +
                '/' + segTag
def imageName = getCurrentImageNameWithoutExtension()
fileName = baseDir + '/detections/' + imageName +
                '_detections_coordinates.json'
File file = new File(fileName)

// Remove file
if (fileExists(fileName)) {
    file.delete()
}

// JSON file metadata
def date = new Date()  // get current date
def timestamp = new SimpleDateFormat('yyyy-MM-dd HH:mm:ss').format(date)  // format date
def towrite = [
    timestamp: timestamp,
    units: 'microns',
    space: atlas
]
towrite['paths'] = [:]  // initialize paths coordinates

getDetectionObjects().forEach(detection -> {  // loop through detections

    // get polyline Geometry
    def geom = detection.getROI().getGeometry()
    def xSlice = geom.getCoordinates().x  // x coordinates
    def ySlice = geom.getCoordinates().y  // y coordinates
    def npoints = xSlice.size()  // number of points in polyline

    // initialize arrays of atlas coordinates
    double[] xAtlas = new double[npoints]
    double[] yAtlas = new double[npoints]
    double[] zAtlas = new double[npoints]
    def hemisphere = []

    xSlice.eachWithIndex { xi, i ->  // loop through (x,y) coordinates

        RealPoint originalPixel = new RealPoint(xi, ySlice[i], 0)  // slice (x,y)
        RealPoint atlasPixel = new RealPoint(3)  // atlas (x,y,z)

        pixelToAtlasTransform.apply(originalPixel, atlasPixel)  // transform pixel coordinates

        // collect results
        if (swapXZFlag) {
            xAtlas[i] = atlasPixel.getDoublePosition(2) * 1000
            yAtlas[i] = atlasPixel.getDoublePosition(1) * 1000
            zAtlas[i] = atlasPixel.getDoublePosition(0) * 1000
        } else {
            xAtlas[i] = atlasPixel.getDoublePosition(0) * 1000
            yAtlas[i] = atlasPixel.getDoublePosition(1) * 1000
            zAtlas[i] = atlasPixel.getDoublePosition(2) * 1000
        }

        // get hemisphere
        if (mirrorLeftRight) {
            if (zAtlas[i] / 1000 > midline) {
                hemisphere.add('Left')
            } else {
                hemisphere.add('Right')
            }
        } else {
            if (zAtlas[i] / 1000 > midline) {
                hemisphere.add('Right')
            } else {
                hemisphere.add('Left')
            }
        }
    }

    def uuid = detection.getID()  // get detection's UUID
    towrite['paths'][uuid] = [
        'x': xAtlas,
        'y': yAtlas,
        'z': zAtlas,
        'hemisphere': hemisphere,
        'skeleton_id': detection.getMeasurements()['skeleton_id'],  // only available if they come from skan
        'length_um': detection.getMeasurements()['Length µm'],
        'classification': detection.getPathClass().toString(),
        'image': imageName
    ]  // store coordinates and info
})

Gson gson = new Gson()
file.write(gson.toJson(towrite))

println(' Done.')

import java.text.SimpleDateFormat
import net.imglib2.RealPoint
import qupath.ext.biop.abba.AtlasTools
import com.google.gson.Gson
