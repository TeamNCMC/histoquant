"""
Script for preprocessing. Does the following :
* Move images from ZEN_EXPORT to Stack_RIP/merged_original, renaming files consistently,
* Split channels in different subdirectories,
* Find the brain mask, save at it as an image, and apply it to channel used for
  detection,
* Apply those masks to other channels.

After checking the previews, if not satisfied with one brain mask, delete it, manually
clean the corresponding image in the reference channel directory with ImageJ, set
`reformat_tf` and `split_tf` to False and run the script again.

Once satisfied with all brain masks, run merge_channels_pyramidal.py to merge cleaned
channel as pyramidal OME-TIFF, ready to be imported into QuPath.

! Double check ALL parameters, especially number of channels and images to mirror !

author : Guillaume Le Goc (g.legoc@posteo.org)
version : 2024.11.19

"""

import os
import re
import sys
import warnings
import xml.etree.ElementTree as ET

import numpy as np
import tifffile
from scipy import ndimage
from skimage import color, feature, measure, morphology, transform
from tqdm import tqdm

# --- Parameters

# definitions
EXPID = "animal0"
CHAN_DETECTION = 1  # index of the channel to use for brain contour detection (1-based)
NCHANNELS = 2  # number of channels

# output image sizes, override maximum size, (nrows, ncolumns). "auto" to find
# automatically based on the whole set of processed images, or None to NOT resize images
FINALSIZE = None

# what to do
# whether to move files, reformatting their names
reformat_tf = False
# whether to split channels -- if True and already done, clean only ref channel
split_tf = False
# whether to find brain mask and clean images from target channel
clean_tf = True
# whether to create downsampled image with masks for control
preview_tf = True
#  whether to apply masks even if the cleaned image already exists
overwrite_cleaned_tf = False

# list of images to mirror (id in original order, as seen in Zen).
# Empty for none, "all" for all, 1-based. Remember range(i, j) stops at j-1
img_to_mirror_lr = []
img_to_mirror_ud = []

# naming convention
IN_PREFIX = "_s"  # prefix before the image number after ZEN export
IN_EXT = "ome.tiff"  # files extension after ZEN export
OUT_PREFIX = ""  # optional prefix, usually empty string -- goes after animal id
OUT_EXT = "ome.tiff"  # output extension for original files
CHAN_EXT = "tiff"  # output extension when splitting channels
OUT_NDIG = 3  # number of digits in output files names

# tiff save options
COMPRESSION = "LZW"  # Tiff compression for split channels, recommended None or LZW
NTHREADS = 18  # number of threads for writing image
IJDESC = {"unit": "um"}  # ImageJ image description

# brain detection parameters
detection_parameters = {
    "bkg": 0,  # estimation of background value
    "cannysigma": np.sqrt(2),  # gaussian sigma in canny edge detection
    "cannythresh": 0.7,  # high threshold in canny edge detection
    "closeradius": 90,  # morphological radius in microns
    "downscale": 5,  # downsampling factor
}

# working directory
WDIR = "/path/to/data"

# --- Functions


def get_tags(page, pixelsize, dtype=np.uint16, compression="LZW"):
    """
    Get the tags from input Tiff file page and returns them as a dictionary.

    The returned dict is meant to be used to write a new tiff page with those tags.
    Some of those tags are set here such as pixel size while the others are read from
    the input Tiff `page`.

    Parameters
    ----------
    page : tifffile.TiffFile.page
    pixelsize : float
        Pixel size in microns.
    compression : str, optional
        Tiff compression (None, LZW, ...). Default is LZW.

    Returns
    -------
    options : dict
        Dictionary with Tiff tags.

    """
    return {
        "shape": (page.imagelength, page.imagewidth),
        "dtype": dtype,
        "bitspersample": page.bitspersample,
        "compression": compression,
        "photometric": page.photometric,
        "planarconfig": page.planarconfig,
        "resolutionunit": page.resolutionunit,
        "resolution": (1 / pixelsize, 1 / pixelsize),
    }


def get_pixelsize_ome(
    desc: str,
    namespace: dict = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"},
) -> float:
    """
    Extract physical pixel size from OME-XML description.

    Raise a warning if pixels are anisotropic (eg. X and Y sizes are not the same).
    Raise an error if size units are not microns ("µm").

    Parameters
    ----------
    desc : str
        OME-XML string from Tiff page.
    namespace : dict, optional
        XML namespace, defaults to latest OME-XML schema (2016-06).

    Returns
    -------
    pixelsize : float
        Physical pixel size.

    """
    root = ET.fromstring(desc)

    for pixels in root.findall(".//ome:Pixels", namespace):
        pixelsize_x = float(pixels.get("PhysicalSizeX"))
        pixelsize_y = float(pixels.get("PhysicalSizeY"))
        break  # stop at first Pixels field in the XML

    # sanity checks
    if pixelsize_x != pixelsize_y:
        warnings.warn(
            f"Anisotropic pixels size found, are you sure ? ({pixelsize_x}, {pixelsize_y})"
        )

    return np.mean([pixelsize_x, pixelsize_y])


def get_pixelsize_ij(tif):
    """
    Get physical pixel size from a Tiff written as ImageJ tiff file.

    The input TiffFile must be a single-page Tiff.

    Parameters
    ----------
    tif : tifffile.TiffFile
        TiffFile object.

    Returns
    -------
    pixelsize : float
        Pixel size in microns.

    """
    xsize, xunit = tif.pages[0].tags["XResolution"].value
    ysize, yunit = tif.pages[0].tags["YResolution"].value

    pixelsize_x = xunit / xsize
    pixelsize_y = yunit / ysize

    # sanity check
    if pixelsize_x != pixelsize_y:
        warnings.warn(
            f"Anisotropic pixels size found, are you sure ? ({pixelsize_x}, {pixelsize_y})"
        )

    return np.mean([pixelsize_x, pixelsize_y])


def extract_image_number(
    filename: str,
    prefix: str = "_s",
    suffix: str = "ome.tiff",
):
    """
    Extract the slice number from its file Zen.

    >>> filename = "gn90_s1.ome.tiff"
    >>> extract_image_number(filename, "_s", "ome.tiff")
    1

    Parameters
    ----------
    filename : str
        File name to extract the number from.
    prefix : str, optional
        Before the number, by default "_s", as in ZEN.
    suffix : str, optional
        After the number (usually the file extension), by default "ome.tiff".

    Returns
    -------
    match : int

    """
    pattern = prefix + "(\\d+)" + "\\." + re.escape(suffix)
    match = re.search(pattern, filename)

    if match:
        return int(match.group(1))
    else:
        warnings.warn(f"Unable to get the slice number from {filename}.")
        return -1  # error code so that the file is skipped


def reformat_filename(expid, slicenum, out_ndig=3, out_prefix="", out_ext="ome.tiff"):
    """
    Generate new standardized file name based on prefix and slice number.

    Parameters
    ----------
    outdir : str
        Output directory.
    expid : str
        Experiement ID.
    slicenum : int
        Slice number.
    out_ndig : int, optional
        Number of digits, filled with zeros. Default is 3.
    out_prefix : str, optional
        Optional prefix after "{animalid}_" and before "{slicenum}.{out_ext}".
    out_ext : str, optional
        Output file extension. Default is "ome.tiff" global variable.

    Returns
    -------
    new_filename : str
        New formatted file name.

    """
    return f"{expid.lower()}_{out_prefix}{str(slicenum).zfill(out_ndig)}.{out_ext}"


def make_outdir_chan(wdir, expid, ichannel, cleaned=False):
    """
    Create directory name wdir/expid/Stack_RIP/ch0{ichannel} or ch0{ichannel}_cleaned.

    Parameters
    ----------
    wdir : str
    expid : str
    ichannel : int
    cleaned : bool, optional
        If True, append _cleaned to the directory name. Default is False.

    Returns
    -------
    outdir : str

    """
    if cleaned:
        return os.path.join(
            wdir, expid, "Stack_RIP", f"ch{str(ichannel).zfill(2)}_cleaned"
        )
    else:
        return os.path.join(wdir, expid, "Stack_RIP", f"ch{str(ichannel).zfill(2)}")


def find_max_size(imgslist):
    """
    Find the maximum image size from a list of full path to image files (TIFF only).

    Only get the metadata without openning the actual image.

    Parameters
    ----------
    imgdir : list
        List of full path to image files.

    Returns
    -------
    maxsize : tuple
        (maximum number of rows, maximum number of columns)

    """
    list_shapes = []  # initialize list of shapes
    for file in imgslist:
        with tifffile.TiffFile(file) as tif:
            list_shapes.append(tif.pages[0].shape)  # add image shape

    # get the max of each columns
    return tuple(np.array(list_shapes).max(axis=0))


def get_max_size(imgslist):
    """
    Wraps find_max_size(imgslist), checking if an override was set.

    """
    # get final image size
    finalsize = FINALSIZE

    # check if final size has to be determined from images
    if finalsize == "auto":
        finalsize = find_max_size(imgslist)

    return finalsize


def split_channels(wdir, expid, imgpath, mirror_lr, mirror_ud):
    """
    Split channels of image `imgpath` and saves them under wdir/expid/Stack_RIP/chXX.

    Parameters
    ----------
    wdir : str
        Working directory.
    expid : str
        Animal ID.
    imgpath : str
        Full path to the image to be splitted.
    mirror_lr : bool
        Whether to mirror the image in the left/right direction (x).
    mirror_ud : bool
        Whether to mirror the image in the up/down direction (y).

    """
    newfilename = os.path.basename(imgpath)  # multi-channel image file name
    ichan = 1  # initialize channel counter (1-based)

    with tifffile.TiffFile(imgpath) as multitif:
        pixelsize = get_pixelsize_ome(multitif.ome_metadata)  # get physical pixel size

        for page in multitif.pages:  # loop through all channels
            # single-channel directory name
            dirchan = make_outdir_chan(wdir, expid, ichan)
            # single-channel file name
            filechan = os.path.join(dirchan, newfilename.replace(".ome", ""))

            # create directory if it does not exist yet
            if not os.path.isdir(dirchan):
                os.makedirs(dirchan)

            # check if output file does not exist
            if os.path.isfile(filechan):
                print("x", end="", flush=True)
                ichan += 1
                continue

            # read & set tags
            options = get_tags(page, pixelsize, compression=COMPRESSION)

            data = page.asarray()  # read channel data

            if mirror_lr:
                data = np.fliplr(data)  # mirror image left/right
            if mirror_ud:
                data = np.flipud(data)  # mirror image up/down

            # write single channel as ImageJ tiff file
            with tifffile.TiffWriter(filechan, imagej=True) as singletif:
                singletif.write(data, metadata=IJDESC, maxworkers=NTHREADS, **options)

            ichan += 1  # increment channel counter for directory name


def find_brain_mask(
    img, bkg=100, cannysigma=np.sqrt(2), cannythresh=0.7, closeradius=182, downscale=10
):
    """
    Find brain contour in input image as a mask.

    Image is binarised using edge detection with Canny method, morphologically closed and filled,
    and the biggest connected component is kept.
    It is highly recommended to downscale the image with the downscale keyword argument to get an
    image with about 4M pixels.

    Parameters
    ----------
    img : np.ndarray
        Input image.
    bkg : int, optional
        Rough estimate of the background. Default is 100.
    cannysigma : float, optional
        Gaussian filter sigma used in Canny method. Default is sqrt(2).
    cannythresh : float <= 1, optional
        High threshold in Canny method, low threshold is 40% of this value. Default is
        0.7.
    closeradius : int, optional
        Radius of the structuring element used for morphological closing, in pixels.
        Default is 182.
    downscale : int, optional
        Downscaling factor. Default is 10.

    Returns
    -------
    mask : np.ndarray
        Binary mask.

    """
    original_shape = img.shape  # original shape of image

    img[img == 0] = bkg  # replace 0 with background to help edge detection

    # downsample image
    img = transform.rescale(
        img, 1 / downscale, anti_aliasing=False, preserve_range=True, order=0
    )

    # edge detection
    img = feature.canny(
        img,
        sigma=cannysigma,
        use_quantiles=True,
        low_threshold=0.4 * cannythresh,
        high_threshold=cannythresh,
    )

    # morphological closing
    footprint = morphology.disk(int(closeradius / downscale))
    img = morphology.binary_closing(img, footprint=footprint)

    # fill holes
    img = ndimage.binary_fill_holes(img)

    # keep biggest object only
    labels = measure.label(img)
    img = labels == np.argmax(np.bincount(labels.flat, weights=img.flat))

    # returned the image in original scale
    return transform.resize(
        img, original_shape, anti_aliasing=False, preserve_range=True, order=0
    )


def apply_brain_mask(img: np.ndarray, mask: np.ndarray, finalsize: tuple | None):
    """
    Apply brain mask to image and pad image to get final size.

    Parameters
    ----------
    img : np.ndarray
        Image.
    mask : np.ndarray
        Logical mask.
    finalsize : tuple or None
        nrows, ncolumns of the final image. If None, no resizing.

    Returns
    -------
    img_cleaned : np.ndarray
        Image limited to mask with finalsize shape.

    """
    mask = mask > 0  # make sure the mask is logical
    img_cleaned = img * mask  # apply mask

    if finalsize is None:
        return img_cleaned
    else:
        return pad_image(img_cleaned, finalsize)  # pad image to get expected size


def clean_image(imgfile: str, maskfile: str, cleanedfile: str, finalsize: tuple | None):
    """
    Apply mask to image. Cleaned image is saved with the same name in cleaned_dir.

    Parameters
    ----------
    imgfile : str
        Full path to image file to be cleaned.
    maskfile : str
        Full path to corresponding mask.
    cleanedfile : str
        Full path to output image.
    finalsize : tuple or None
        (nrows, ncolumns) of final image. If None, no resizing.

    """
    # read input image
    with tifffile.TiffFile(imgfile) as tif:
        pixelsize = get_pixelsize_ij(tif)
        img = tif.pages[0].asarray()
    # read mask
    mask = tifffile.imread(maskfile)
    # apply mask
    imgcleaned = apply_brain_mask(img, mask, finalsize)

    with tifffile.TiffWriter(cleanedfile, imagej=True) as cleantif:
        # write cleaned image
        cleantif.write(
            imgcleaned,
            metadata=IJDESC,
            maxworkers=NTHREADS,
            compression=COMPRESSION,
            resolution=(1 / pixelsize, 1 / pixelsize),
        )


def create_preview_overlay(img, mask, downscale=50, **kwargs):
    """
    Create an RGB image with image in grayscale and the mask overlaid in transparency.

    The image can be downscaled since it's only for preview purposes.

    Parameters
    ----------
    img : np.ndarray
    mask : np.ndarray
    downscale : int, optional
        Downscaling factor. Default is 50.
    **kwargs : passed to skimage.color.label2rgb

    Returns
    -------
    preview_overlay : np.ndarray
        RGB image.

    """

    # downsample image and mask
    img = transform.rescale(
        img, 1 / downscale, anti_aliasing=False, preserve_range=True, order=0
    )
    mask = transform.rescale(
        mask, 1 / downscale, anti_aliasing=False, preserve_range=True, order=0
    )

    img = img / img.max()  # normalize image

    preview_overlay = color.label2rgb(mask, image=img, **kwargs)  # get overlay
    preview_overlay = preview_overlay / preview_overlay.max() * 255  # normalize

    return preview_overlay.astype("uint8")


def get_brain_mask(
    imgfile: str,
    maskfile: str,
    cleanedfile: str,
    finalsize: tuple | None,
    preview: bool = True,
    preview_downscale: int = 20,
    **kwargs,
):
    """
    Find brain mask for image filename and saves it in masks_dir.

    Apply the mask on the image and save the masked image while we're at it.

    Parameters
    ----------
    imgfile : str
        Full path to the image file.
    maskfile : str
        Full path to the output brain mask.
    cleanedfile : str
        Full path to the output cleaned image file.
    finalsize : tuple or None
        (nrows, ncolumns), expected shape of cleaned image, if None, do not resize the
        image.
    preview : bool, optional
        Create downscaled version of mask. Default is True.
    preview_downscale : int, optional
        Downsampling factor for previews. Default is 20.
    **kwargs : passed to find_brain_mask()

    """
    # read input image
    with tifffile.TiffFile(imgfile) as tif:
        pixelsize = get_pixelsize_ij(tif)
        img = tif.pages[0].asarray()
    # get brain mask
    mask = find_brain_mask(img, **kwargs)

    tifffile.imwrite(
        maskfile,
        mask,
        photometric="minisblack",
        maxworkers=NTHREADS,
    )  # save mask

    # apply mask on detection channel
    imgcleaned = apply_brain_mask(img, mask, finalsize)  # apply brain mask

    with tifffile.TiffWriter(cleanedfile, imagej=True) as cleantif:
        cleantif.write(
            imgcleaned,
            metadata=IJDESC,
            maxworkers=NTHREADS,
            resolution=(1 / pixelsize, 1 / pixelsize),
        )  # write cleaned image

    # create downsampled preview
    if preview:
        previewfile = os.path.join(
            os.path.split(maskfile)[0], "Previews", os.path.basename(maskfile)
        )

        preview_overlay = create_preview_overlay(
            img, mask, downscale=preview_downscale, bg_label=0, alpha=0.1
        )  # create preview

        tifffile.imwrite(
            previewfile, preview_overlay, photometric="rgb", maxworkers=NTHREADS
        )  # save preview


def pad_image(img: np.ndarray, finalsize: tuple):
    """
    Pad image with zeroes to match expected final size.

    Parameters
    ----------
    img : np.ndarray
    finalsize : tuple
        nrows, ncolumns

    Returns
    -------
    imgpad : np.ndarray
        img with black borders.

    """

    final_h = finalsize[0]  # requested number of rows (height)
    final_w = finalsize[1]  # requested number of columns (width)
    original_h = img.shape[0]  # input number of rows
    original_w = img.shape[1]  # input number of columns

    a = (final_h - original_h) // 2  # vertical padding before
    aa = final_h - a - original_h  # vertical padding after
    b = (final_w - original_w) // 2  # horizontal padding before
    bb = final_w - b - original_w  # horizontal padding after

    return np.pad(img, pad_width=((a, aa), (b, bb)), mode="constant")


def process_directory(
    expid: str,
    nchannels: int = None,
    detection_parameters: dict = {},
    mirror_indices_lr: str | list | None = None,
    mirror_indices_ud: str | list | None = None,
    move: bool = True,
    split: bool = True,
    clean: bool = True,
    preview: bool = True,
    overwrite: bool = False,
):
    """
    Main function. Rename files, split channels, find brain contours and apply them.

    - Move files from WDIR/expid/ZEN_EXPORT to WDIR/expid/Stack_RIP/merged_original,
    renaming the files so that they are sorted with consistent numbering;
    - Split channels and put individual channels in chXX directories, so that they can
    be edited in Fiji if needed;
    - Find brain contours on specified channel in each slice and save it as a mask
    image;
    - Apply those brain contours on other channels.

    Parameters
    ----------
    expid : string
        Experiment ID.
    nchannels : int
        Number of channels. Required in case the script is ran after splitting channels.
    detection_parameters : dict
        Parameters for brain detection, passed as **kwargs.
    mirror_indices_lr : list, str or None, optional
        Images to mirror left/right. Can be a list of indices or "all" or None. Default
        is None.
    mirror_indices_ud : list, str or None, optional
        Same as `mirror_indices_lr`, in the vertical direction (up/down).
    move : bool, optional
        Move and reformat file names. Default is True.
    split : bool, optional
        Split channels or not. Default is True.
    clean : bool, optional
        Find brain masks or not. Default is True.
    preview : bool, optional
        Create brain masks preview or not. Default is True.
    overwrite : bool, optional
        If True, apply the brain masks even if the cleaned image already exists. Default is False.

    """
    # --- Preparation ---
    wdir = os.path.abspath(WDIR)

    # build directories names
    inpdir = os.path.join(wdir, expid, "ZEN_EXPORT")
    outdir = os.path.join(wdir, expid, "Stack_RIP", "merged_original")

    # create directory if it does not exist
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    if move or split:
        # list files, natural sorted
        fileslist = os.listdir(inpdir)
        list_files = [
            filename for filename in fileslist if filename.endswith("." + IN_EXT)
        ]

        nfiles = len(list_files)
        # flag to determine how the slice number will be extracted
        already_moved = False
        if nfiles == 0:  # check if there are files to process
            if move:  # there are no files to move
                print("No files found in the input directory.")
                sys.exit()
            else:  # look for files in output directory to split channels instead
                fileslist = os.listdir(outdir)
                list_files = [
                    filename for filename in fileslist if filename.endswith(OUT_EXT)
                ]
                nfiles = len(list_files)
                already_moved = True
                if nfiles == 0:  # still no files, exiting
                    print("No files found.")
                    sys.exit()

        # sort out what images are going to be flipped
        elif mirror_indices_lr is None:
            mirror_indices_lr = []  # translate None as no images
        elif mirror_indices_ud is None:
            mirror_indices_ud = []  # translate None as no images

        # -----------------------------------------------------------------------------------

        # --- Rename files and split channels ---
        pbar = tqdm(list_files)
        for filename in pbar:
            # make file names
            oldpath = os.path.join(inpdir, filename)
            # get image number
            if not already_moved:
                # filename from Zen, with defined prefix and suffix
                ifile = extract_image_number(filename, prefix=IN_PREFIX, suffix=IN_EXT)
                if ifile == -1:
                    continue
            else:
                # filename already formatted, with standardized prefix and suffix
                ifile = extract_image_number(
                    filename, prefix=expid.lower() + "_" + OUT_PREFIX, suffix=IN_EXT
                )
                if ifile == -1:
                    continue

            # get formatted file name
            newfilename = reformat_filename(
                expid, ifile, out_ndig=OUT_NDIG, out_prefix=OUT_PREFIX, out_ext=OUT_EXT
            )
            # corresponding full path
            newpath = os.path.join(outdir, newfilename)

            # check if file does not exist already and move it with the new name
            if (not os.path.isfile(newpath)) and move:
                pbar.set_description(f"Renaming and splitting channels of {filename}")
                os.rename(oldpath, newpath)
            elif (os.path.isfile(newpath)) and move:
                continue

            # split channels
            if split:
                # check if mirroring needs to be performed
                if (mirror_indices_lr == "all") or (ifile in mirror_indices_lr):
                    mirror_lr = True
                else:
                    mirror_lr = False
                if (mirror_indices_ud == "all") or (ifile in mirror_indices_ud):
                    mirror_ud = True
                else:
                    mirror_ud = False

                split_channels(
                    wdir,
                    expid,
                    newpath,
                    mirror_lr,
                    mirror_ud,
                )

    # ---------------------------------------------------------------------------------------

    # --- Find brain masks ---
    if clean:
        # directory of the channel on which we find the brain mask
        channel_detection_dir = make_outdir_chan(wdir, expid, CHAN_DETECTION)

        # masks directory
        masks_dir = os.path.join(wdir, expid, "Stack_RIP", "Masks")

        # cleaned images directory
        cleaned_dir = make_outdir_chan(wdir, expid, CHAN_DETECTION, cleaned=True)

        # create directories if they don't exist already
        if not os.path.isdir(masks_dir):
            os.mkdir(masks_dir)
        if not os.path.isdir(cleaned_dir):
            os.mkdir(cleaned_dir)
        if (not os.path.isdir(os.path.join(masks_dir, "Previews"))) and preview:
            os.mkdir(os.path.join(masks_dir, "Previews"))

        # list images
        fileslist = [
            os.path.join(channel_detection_dir, file)
            for file in os.listdir(channel_detection_dir)
            if file.endswith(CHAN_EXT)
        ]

        # find final image size
        finalsize = get_max_size(fileslist)

        # get brain masks
        pbar = tqdm(fileslist)
        for imgfile in pbar:
            # make file names
            base_filename = os.path.splitext(os.path.basename(imgfile))[0]
            maskfile = os.path.join(masks_dir, base_filename + ".tiff")
            cleanedfile = os.path.join(cleaned_dir, base_filename + ".tiff")

            pbar.set_description(f"Getting brain masks of {base_filename}")

            # skip only if the brain mask exists already
            if os.path.isfile(maskfile):
                continue

            get_brain_mask(
                imgfile,
                maskfile,
                cleanedfile,
                finalsize=finalsize,
                preview=preview,
                preview_downscale=20,
                **detection_parameters,
            )

        # --- Apply brain masks ---
        channels = [
            *range(1, nchannels + 1)
        ]  # keep detection channel in case it needs to be re-applied
        pbar_channels = tqdm(channels)
        for chanid in pbar_channels:
            pbar_channels.set_description(f"Applying masks on channel {chanid}")

            # channel directory
            channel_dir = make_outdir_chan(wdir, expid, chanid)

            # cleaned image directory
            cleaned_dir = make_outdir_chan(wdir, expid, chanid, cleaned=True)

            # create directory if it doesn't exist already
            if not os.path.isdir(cleaned_dir):
                os.mkdir(cleaned_dir)

            # list images
            fileslist = [
                os.path.join(channel_dir, file)
                for file in os.listdir(channel_dir)
                if file.endswith(CHAN_EXT)
            ]

            # apply brain mask
            pbar_files = tqdm(fileslist)
            for imgfile in pbar_files:
                # make file names
                base_filename = os.path.splitext(os.path.basename(imgfile))[0]
                maskfile = os.path.join(masks_dir, base_filename + ".tiff")
                cleanedfile = os.path.join(cleaned_dir, base_filename + ".tiff")

                # skip if file already exists and overwriting is off
                if (not overwrite) & (os.path.isfile(cleanedfile)):
                    continue

                pbar_files.set_description(f"Processing {base_filename}")

                clean_image(imgfile, maskfile, cleanedfile, finalsize)

            pbar.set_description("Done.")


# --- Call
if __name__ == "__main__":
    process_directory(
        EXPID,
        detection_parameters=detection_parameters,
        nchannels=NCHANNELS,
        mirror_indices_lr=img_to_mirror_lr,
        mirror_indices_ud=img_to_mirror_ud,
        move=reformat_tf,
        split=split_tf,
        clean=clean_tf,
        preview=preview_tf,
        overwrite=overwrite_cleaned_tf,
    )
