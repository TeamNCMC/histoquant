/**
 * batchConvertClassification.groovy
 *
 * Convert detections various classifications to a single one. This could be used in
 * pipelineImportExport.groovy instead of the single-classification conversion (lines #154-159).
 */

def classesToConvert = ["Fibers: DsRed", "Fibers: EGFP", "Fibers: Cy5"]
def newClass = "Fibers: Triple"

getDetectionObjects().findAll {
    it.getPathClass().toString() in classesToConvert}
    .forEach { it.setPathClass(getPathClass(newClass)) }