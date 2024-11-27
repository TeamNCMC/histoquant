/**
 * importImageJRois.groovy
 *
 * Import ImageJ ROIs (.roi or .zip).
 * File names should match the current image name. The new annotations will be classified
 * as their name.
 */

// Parameters
def roiDirPath = "/path/to/rois"

// Build file name
def imageName = getCurrentImageNameWithoutExtension()
def fileName = buildFilePath(roiDirPath, imageName + ".roi")
file = new File(fileName)
if (!file.exists()) {
    fileName = buildFilePath(roiDirPath, imageName + ".roi.zip")
    file = new File(fileName)
}

// Get annotations that are already there
def annotationsBeforeImport = getAnnotationObjects()

// Read ROIs
rois = IJTools.readImageJRois(file)

// Prepare import parameters
def downsample = 1.0
def xOrigin = 0.0
def yOrigin = 0.0

// Import
def pathObjects = rois.stream().map(r -> IJTools.convertToAnnotation(r, xOrigin, yOrigin, downsample, null)).toList();
addObjects(pathObjects)

// Get the new annotations
def newAnnotations = getAnnotationObjects() - annotationsBeforeImport

// Set classification to their name
newAnnotations.forEach{
    it.setPathClass(getPathClass(it.getName()))
}

// Update hierarchy
resolveHierarchy()
fireHierarchyUpdate()