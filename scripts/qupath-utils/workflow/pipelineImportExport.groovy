/**
 * pipelineImportExport.groovy
 *
 * Wraps other analysis script to do everything at once :
 * - clear all objects
 * - import ABBA regions
 * - mirror regions names
 * - import geojson detections (from $folderPrefix$segmentation/$segTag$/geojson)
 * - add measurements to detections
 * - add atlas coordinates to detections
 * - add hemisphere to detections' parents
 * - add regions measurements (count for punctal objects, cumulated length for lines objects)
 * - export detections measurements (points and polygons) as CSV
 * - export detections measurements (polylines) as JSON
 * - export annotations as CSV
 *
 * For one image, two files are generated, one for detections and one for annotations.
 * Detections (annotations) files will be stored in, relative to the QuPath project parent directory :
 * $folderPrefix$segmentation/$segTag$/detections(annotations)
 * where $folderPrefix$ and $segTag$ are defined below.
 * WARNING - it overwrites any file being written !
 * WARNING - it clears all objects !
 */

// --- Parameters
def atlasType = 'brain'  // type of registration, "brain" or "cord"
def folderPrefix = 'id_' // output folder name, "segmentation" will be appended
def segTag = 'cells'  // type of segmentation

// detections classifications to be exported (must be an ArrayList [])
def exportedDetections = ['Cells: marker+']

// convert detections classifications beforehand
def convertDetectionClassifications = false
def classToConvert = 'Cells'
def newClass = 'Cells: marker+'

def regionNames = 'acronym'  // import ABBA regions as "acronym" or "name"

// --- Preparation
// Build output directory name
def projectParentDir = new File(buildFilePath(PROJECT_BASE_DIR)).getParent()
def baseDir = projectParentDir +
                '/' + folderPrefix + 'segmentation' +
                '/' + segTag
def imageName = getCurrentImageNameWithoutExtension()
def imageData = getCurrentImageData()

// check directory
File baseDirCheck = new File(baseDir)
if (!baseDirCheck.exists()) {
    throw new Exception("Segmentation directory does not exist, check 'folderPrefix' and 'segTag'.")
}

// fill atlas details based on registration type
def mirrorLeftRight
def midline
def swapXZFlag
if (atlasType == 'brain') {
    mirrorLeftRight = true  // mirror hemisphere. CCFv3 is mirrored, spinal cord is not
    midline = 5.70  // left/right medio-lateral limit in CCFv3 in mm
    swapXZFlag = false  // X and Z are not swapped with regular ABBA in Fiji
} else if (atlasType == 'cord') {
    mirrorLeftRight = false
    midline = 1.61  // left/right medio-lateral limit in spinal cord in mm
    swapXZFlag = true  // X and Z are swapped with ABBA from python
} else {
    throw new Exception("atlasType not supported, choose either 'brain' or 'cord'.")
}

// prepare segementation types
fiberLikeSeg = ['fibers', 'axons', 'fiber', 'axon']
cellLikeSeg = ['synapto', 'synaptophysin', 'syngfp', 'boutons', 'points', 'cells', 'polygons', 'polygon', 'cell']

if (segTag !in fiberLikeSeg + cellLikeSeg) {
    throw new Exception("'setTag' not supported, add it to either 'fiberLikeSeg' or 'cellLikeSeg' in the script.")
}

println('------------------')
println('|--- ' + imageName + ' ---|')
println('------------------')

// --- Cleanup
print('Deleting everything...')
clearAllObjects()
println(' Done.')

// --- Import ABBA
def pixelToAtlasTransform
def transformFlag
try {
    // this should error if there is no registration
    pixelToAtlasTransform =
        AtlasTools
        .getAtlasToPixelTransform(imageData)
        .inverse()  // pixel to atlas = inverse of atlas to pixel

    // we can transform coordinates
    transformFlag = true
} catch (Exception e) {
    // there is no registration at all
    transformFlag = false
    println('[Warning] No ABBA registration found.')
}

print('Importing ABBA regions...')
def atlasFlag
try {
    AtlasTools.loadWarpedAtlasAnnotations(imageData, regionNames, true) // load brain regions
    atlasFlag = true
    println(' Done.')
} catch (Exception e) {
    atlasFlag = false
    println('[Warning] No regions to import.')
}

// --- Mirror regions hemisphere (left/right)
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

// --- Import detections
print('Importing detections...')
// Build files names
def fileNames = new File(baseDir + '/geojson/')
        .listFiles()
        .findAll {
            it.name.startsWith(imageName) && it.name.endsWith('.geojson')
        }
        *.name

if (fileNames.size() == 0) {
    println('[Warning] No detections file found.')
}

// Import objects from files
for (fileName in fileNames) {
    importObjectsFromFile(baseDir + '/geojson/' + fileName)
}

// Insert in hierarchy
insertObjects(getDetectionObjects())
fireHierarchyUpdate()

// Convert classifications if required
if (convertDetectionClassifications) {
    getDetectionObjects().findAll {
        it.getPathClass().toString() == classToConvert}
        .forEach { it.setPathClass(getPathClass(newClass)) }
}
println(' Done.')

// --- Add measurements
print('Adding shape measurements...')
addShapeMeasurements(imageData, getDetectionObjects(),
    'AREA', 'LENGTH', 'CIRCULARITY', 'SOLIDITY', 'MAX_DIAMETER', 'MIN_DIAMETER')
println(' Done.')

// Add cumulated length in each brain regions
if (atlasFlag && segTag in fiberLikeSeg) {
    print('Adding fibers length per region...')
    // Get pixel size
    def pixelSize = getCurrentServer().getPixelCalibration().getAveragedPixelSizeMicrons()

    // Loop through detections that are to be exported
    for (exportedDetection in exportedDetections) {
        // Get objects of interest
        def regions = getAnnotationObjects()
            .findAll { it.getROI().isArea() }  // get brain regions
        def detections = getDetectionObjects()
            .findAll { it.getPathClass().toString() == exportedDetection }  // get selected detection type
        def detectionsUnion = RoiTools.union(detections.collect { it.getROI() })  // create a ROI combining all detections

        for (region in regions) {
            def regionROI = region.getROI() // get region ROI
            def length = RoiTools.intersection(detectionsUnion, regionROI).getLength()  // compute total length
            def length_um = length * pixelSize  // convert to microns
            region.measurements.put(exportedDetection + " Length µm", length_um)
        }
    }
    println(' Done')
}

// Add object count in each regions
if (atlasFlag && segTag in cellLikeSeg) {
    print('Adding objects count per region...')

    // Loop through detections that are to be exported
    for (exportedDetection in exportedDetections) {
        // Get objects of interest
        def regions = getAnnotationObjects()
            .findAll { it.getROI().isArea() }  // get brain regions

        for (region in regions) {
            def count = countDetectionsInAnnotation(region, exportedDetection)
            region.measurements.put(exportedDetection + ' Count', count)
        }
    }
    println(' Done')
}

// --- Add atlas coordinates
if (transformFlag && segTag !in fiberLikeSeg) {
    print('Adding Atlas coordinates...')

    getDetectionObjects().forEach(detection -> {
        RealPoint atlasCoordinates = new RealPoint(3)
        MeasurementList ml = detection.getMeasurementList()
        atlasCoordinates.setPosition([detection.getROI().getCentroidX(), detection.getROI().getCentroidY(), 0] as double[])
        pixelToAtlasTransform.apply(atlasCoordinates, atlasCoordinates)
        if (swapXZFlag) {
            ml.put('Atlas_X', atlasCoordinates.getDoublePosition(2) * 1000)  // convert to microns
            ml.put('Atlas_Y', atlasCoordinates.getDoublePosition(1) * 1000)
            ml.put('Atlas_Z', atlasCoordinates.getDoublePosition(0) * 1000)
        } else {
            ml.put('Atlas_X', atlasCoordinates.getDoublePosition(0) * 1000)  // convert to microns
            ml.put('Atlas_Y', atlasCoordinates.getDoublePosition(1) * 1000)
            ml.put('Atlas_Z', atlasCoordinates.getDoublePosition(2) * 1000)
        }
    })
    println(' Done.')
}

// --- Add hemisphere to detections' parents
if (atlasFlag && segTag !in fiberLikeSeg) {
    print('Adding hemispheres...')
    getDetectionObjects().forEach {
        def parent = it.getParent()
        if (parent != null) {
            if (parent.getPathClass().isDerivedFrom(getPathClass('Left'))) {
                it.setName('Left: ' + it.getClassifications()[0])
            }
            else if (parent.getPathClass().isDerivedFrom(getPathClass('Right')))
                it.setName('Right: ' + it.getClassifications()[0])
        }
    }
    println(' Done.')
}

// --- Export detections
print('Exporting detections...')
// Build file name
fileName = baseDir + '/detections/' + imageName +
                '_detections_measurements.csv'

// Check dir exists
File dirdet = new File(baseDir + '/detections/')
if (!dirdet.exists()) {
    dirdet.mkdirs()
}

// Export detection measurements
saveDetectionMeasurements(fileName)
println(' Done.')

// --- Export detections CCFv3 coordinates for fibers-like objects
if (transformFlag && segTag in fiberLikeSeg) {
    print('Exporting fibers coordinates...')
    // Build file name
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
        space: 'CCFv3'
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
            'skeleton_id': detection.getMeasurements()['skeleton_id'],
            'length_um': detection.getMeasurements()["Length µm"],
            'classification': detection.getPathClass().toString(),
            'image': imageName
        ]  // store coordinates and info
    })

    Gson gson = new Gson()
    file.write(gson.toJson(towrite))

    println(' Done.')
}

// --- Export annotations
print('Exporting annotations...')
// Build file name
fileName = baseDir + '/annotations/' + imageName +
                '_annotations_measurements.csv'

// Check dir exists
File dirann = new File(baseDir + '/annotations/')
if (!dirann.exists()) {
    dirann.mkdirs()
}

// Export annotations measurements
saveAnnotationMeasurements(fileName)
println(' Done.')

println('All done !')

// Helper functions
def countDetectionsInAnnotation(annotation, classification) {
    // function that counts detections of classification `classification` in `annotation`.
    return annotation.getChildObjects().findAll {
        (it.getPathClass().toString() == classification) &
        (it.isDetection())
    }.size()
}

import java.text.SimpleDateFormat
import net.imglib2.RealPoint
import qupath.ext.biop.abba.AtlasTools
import qupath.lib.measurements.MeasurementList
import com.google.gson.Gson
