/**
 * exportPixelClassifierProbabilities.groovy
 *
 * Export probabilities maps from a pixel classifier.
 * Generates tif image with n channels, one for each classes.
 * Output images will be stored in, relative to the QuPath project parent directory :
 * $folderPrefix$segmentation/$segTag$/probabilities
 * where $folderPrefix$ and $segTag$ are defined below.
 * Output images name will be the original image name with "_Probabilities.tiff" appended.
 */

// Parameters
def classifierName = 'classifier_name'  // classifier name, must match an existing one within the QuPath project
def folderPrefix = 'id_'  // output folder name, "segmentation" will be appended
def segTag = 'fibers'  // type of segmentation

// Build output directory name
def projectParentDir = new File(buildFilePath(PROJECT_BASE_DIR)).getParent()
def outputDir = projectParentDir +
                '/' + folderPrefix + 'segmentation' +
                '/' + segTag +
                '/' + 'probabilities/'

// Build file name from image name
def imageName = getCurrentImageNameWithoutExtension()
def fileName = outputDir + imageName + '_Probabilities.tiff'

// Check if directory exists
File dir = new File(outputDir)
if (!dir.exists()) {
    dir.mkdirs()
}

// Write probabilities image
print(imageName + ' - Exporting probability map...')
writePredictionImage(classifierName, fileName)
print('Done !')
