/**
 * setClassificationAsName.groovy
 *
 * Set all classifications' names to their derived classification.
 */

getAnnotationObjects().findAll {
    it.setName(it.getClassifications()[-1])}
