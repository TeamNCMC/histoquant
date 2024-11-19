/**
 * findClassification.groovy
 *
 * Find in which image there is an annotation with given annotation.
 */

// region to find
def classToFind = 'Region*'

// look for regions that has the specified name
matchingObjects = getAllObjects().findAll { it.getPathClass().toString() == classToFind }

// get image name
def entry = getProjectEntry()
def imageName = entry.getImageName()

// print if found
if (matchingObjects) {
    println(classToFind + ' found in ' + imageName)
}

selectObjects(matchingObjects)
