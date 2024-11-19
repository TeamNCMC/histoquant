/**
 * findRegion.groovy
 *
 * Find in which image there is an annotation with given name.
 */

// region to find
def regionToFind = 'DTN'

// look for regions that has the specified name
matchingObjects = getAllObjects().findAll { it.getName() == regionToFind }

// get image name
def entry = getProjectEntry()
def imageName = entry.getImageName()

// print if found
if (matchingObjects) {
    println(regionToFind + ' found in ' + imageName)
}

selectObjects(matchingObjects)
