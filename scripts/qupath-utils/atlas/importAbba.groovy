/**
 * importAbba.groovy
 *
 * Import atlas regions as annotations from ABBA.
 * Optionnaly flip left/right regions names.
 * It requires the ABBA extension, and registration exported to the QuPath project.
 *
 * Warning : it will remove all annotations.
 */

// Flip Left / Right regions names.
def mirrorLeftRight = true

removeObjects(getAnnotationObjects(), true) // last argument = keep child objects ?
AtlasTools.loadWarpedAtlasAnnotations(getCurrentImageData(), 'acronym', true)

// Mirror if required
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

import qupath.ext.biop.abba.AtlasTools
