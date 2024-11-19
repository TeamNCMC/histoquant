/**
 * createDetectionsFromPixelClassifier.groovy
 *
 * Create detections from pixel classifier.
 */

// Parameters
def classifierName = 'classifier-name'  // name of the pixel classifier
def minArea = 40  // minimum area in microns^2
def minHoleArea = 10000  // holes below this size will be filled

// create detections only in annotations with this classificiation. Set to -1 for all imagee
def roiClassification = 'ROI'

// Processing
if (roiClassification != -1) {
    selectObjectsByPathClass(getPathClass(roiClassification))
}
createDetectionsFromPixelClassifier(classifierName, minArea, minHoleArea, 'SPLIT')
