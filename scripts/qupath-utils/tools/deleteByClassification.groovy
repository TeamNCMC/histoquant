/**
 * deleteByClassification.groovy
 *
 * Delete all objects whose class correspondond to the specified one.
 * To delete objects whose class is empty, set an empty string.
 */

// Define what class to delete
def classToDelete = 'Cells: markerX'

// Find corresponding objects
if (classToDelete.isEmpty()) {
    toRemove = getAllObjects().findAll { it.getPathClass().toString().isEmpty() }
} else {
    toRemove = getAllObjects().findAll { it.getPathClass().toString() == classToDelete }
    // Uncomment below to delete all objects that CONTAINS the class name -- use with caution
    //def toremove = getAllObjects().findAll{it.getPathClass().toString().contains(classToDelete)}
}

// remove selected objects
removeObjects(toRemove, true)
