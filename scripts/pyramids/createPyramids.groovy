/**
 * createPyramids.groovy
 *
 * Convert OME-TIFF to pyramidal OME-TIFF, using QuPath.
 * See 'create_pyramids.py' python script to call this script in batch from python.
 *
 * author : Guillaume Le Goc (g.legoc@posteo.org) @ NeuroPSI
 * version : 2024.08.30
 */

// --- Parameters
def compression = OMEPyramidWriter.CompressionType.LZW  // compression (lossless)

// parse input arguments
def uid = args[0]
def tileSize = args[1] as int // TIFF tile size
def pyramidScaling = args[2] as int // factor between two consecutive pyramid level
def nThreads = args[3] as int // number of threads for parallelization

// --- Preparation

// get QuPath image server
def server = getCurrentServer()

// define input and output file names
def imagePath = server.getBuilder().getURIs()[0].getPath()
File imageFile = new File(imagePath)
def newImageName = uid + '_' + imageFile.getName().toString()
def outputPath = new File(imageFile.getParent().toString(), newImageName).toString()

// --- Write the new pyramidal tiff
new OMEPyramidWriter.Builder(server)
        .parallelize(nThreads)
        .tileSize(tileSize)
        .scaledDownsampling(1, pyramidScaling) // 1 : full resolution
        .compression(compression)
        .build()
        .writePyramid(outputPath)

// --- Imports
import qupath.lib.images.writers.ome.OMEPyramidWriter
import qupath.lib.images.servers.*
import javax.imageio.*
import qupath.lib.images.servers.ImageServerMetadata
