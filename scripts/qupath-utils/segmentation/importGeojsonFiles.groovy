/**
 * importGeojsonFiles.groovy
 *
 * Import detections stored as geojson files.
 * The geojson files must have the same name as the image detections will be imported
 * into. Used to import when segmentation happened outside QuPath.
 */

// Path to the directory with geojson files, including the trailing "/"
def geojsonDir = '/path/to/geojson/files/'

// Build files names
def imageName = getCurrentImageNameWithoutExtension()
def fileNames = new File(geojsonDir)
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
    importObjectsFromFile(geojsonDir + fileName)
}

// Insert in hierarchy
insertObjects(getDetectionObjects())
fireHierarchyUpdate()
