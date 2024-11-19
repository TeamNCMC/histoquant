/**
 * addHemisphereToDetections.groovy
 *
 * Add hemisphere to detections names.
 * The hemisphere is determined based on the detection parent, the latter must
 * have a classification derived from "Left" or "Right".
 */

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
