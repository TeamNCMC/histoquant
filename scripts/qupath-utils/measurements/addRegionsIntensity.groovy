/**
 * addRegionsIntensity.groovy
 *
 * Add the mean or median intensity in each channel in each annotation.
 * Adds it as "classification: channel mean" or "classification: channel median"
 *
 */

// Name of the main classification
def classificationName = 'Fibers'
// Names of the channels to use. They must be the channels actual names in the project (case sensitive)
def channelsNames = ['Cy5', 'DsRed', 'EGFP']
// What to compute, "MEAN" or "MEDIAN", in full caps
def metric = 'MEDIAN'
// Remember : the measurement names will be "$classificatioName: $channelName$ $metric$"

// Prepare data
def server = getCurrentServer()
def measurements = [ObjectMeasurements.Measurements.valueOf(metric)] as List
def compartments = ObjectMeasurements.Compartments.values() as List
def downsample = 1.0
def regions = getAnnotationObjects()
def allChannelsNames = server.getMetadata().getChannels().collect { it.getName() }

// Measure
for (region in regions) {
    ObjectMeasurements.addIntensityMeasurements(
        server, region, downsample, measurements, compartments
    )
    // This adds measurements called "$channelName$: $metric$", so some clean up is in order
    measurementsList = region.getMeasurementList()

    for (channelName in allChannelsNames) {
        // Build measurement name
        measurementName = channelName + ': ' + metric.toLowerCase().capitalize()
        if (!channelsNames.contains(channelName)) {
            // If not required, delete it
            region.measurements.remove(measurementName)
        } else {
            // Rename it
            newName = classificationName + ': ' + channelName + ' ' + metric.toLowerCase().capitalize()
            value = region.measurements.get(measurementName)
            region.measurements.remove(measurementName)
            region.measurements.put(newName, value)
        }
    }
}

import qupath.lib.analysis.features.ObjectMeasurements
