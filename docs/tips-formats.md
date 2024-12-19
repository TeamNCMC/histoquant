# Data format

## Some concepts
### Tiles
The representation of an image in a computer is basically a table where each element represents the pixel value (see more [here](https://bioimagebook.github.io/chapters/1-concepts/1-images_and_pixels/images_and_pixels.html)). It can be n-dimensional, where the typical dimensions would be \((x, y, z)\), time and the fluorescence channels.

In large images, such as histological slices that are more than 10000\(\times\)10000 pixels, a strategy called *tiling* is used to optimize access to specific regions in the image. Storing the whole image at once in a file would imply to load the whole thing at once in the memory (RAM), even though one would only need to access a given rectangular region with a given zoom. Instead, the image is stored as *tiles*, small squares (512--2048 pixels) that pave the whole image and are used to reconstruct the original image. Therefore, when zooming-in, only the relevant tiles are loaded and displayed, allowing for smooth large image navigation. This process is done seamlessly by software like QuPath and BigDataViewer (the Fiji plugin ABBA is based on) when loading tiled images. This is also leveraged for image processing in QuPath, which will work on tiles instead of the whole image to not saturate your computer RAM.

Most images are already tiled, including Zeiss CZI images. Note that those tiles do not necessarily correspond to the actual, real-world, tiles the microscope did to image the whole slide.

### Pyramids
In the same spirit as tiles, it would be a waste to have to load the entire image (and all the tiles) at once when viewing the image at max zoom-out, as your monitor nor your eyes would handle it. Instead, smaller, rescaled versions of the original image are stored alongside it, and depending on the zoom you are using, the sub-resolution version is displayed. Again, this is done seamlessly by QuPath and ABBA, allowing you to quickly switch from an image to another, without having to load the GB-sized image. Also, for image processing that does not require the original pixel size, QuPath can also leverage pyramids to go faster.

Usually, upon openning a CZI file in ZEN, there is a pop-up suggesting you to generate pyramids. It is a *very* good idea to say yes, wait a bit and save the file so that the pyramidal levels are saved within the file.

### Metadata
Metadata, while often overlooked, are of paramount importance in microscopy data. It allows both softwares and users to interpret the raw data of images, eg. the values of each pixels. Most image file formats support this, including the microcope manufacturer file formats. Metadata may include :

- Pixel size. Usually expressed in µm for microscopy, this maps computer pixel units into real world distance. QuPath and ABBA uses that calibration to scale your image properly, so that it match the atlas you'll register your slices on,
- Channels colors and names,
- Image type (fluorescence, brightfield, ...),
- Dimensions,
- Magnification...

Pixel size is *the* parameter that is absolutely necessary. Channel names and colors are more a quality of life feature, to make sure not to mix your difference fluorescence channels. CZI files or exported OME-TIFF files include this out of the box so you don't really need to pay attention.

## Bio-formats
[Bio-formats](https://www.openmicroscopy.org/bio-formats/) is an initiative of the Open Microscopy Environment (OME) consortium, aiming at being able to read proprietary microscopy image data *and* metadata. It is used in QuPath, Fiji and ABBA.

[This page](https://bio-formats.readthedocs.io/en/latest/supported-formats.html) summarizes the level of support of numerous file formats. You can see that Zeiss CZI files and Leica LIF are quite well supported, and *should* therefore work out of the box in QuPath.

## Zeiss CZI files
QuPath and ABBA supports any Bio-formats supported, tiled, pyramidal images.

If you're in luck, adding the pyramidal CZI file to your [QuPath project](https://qupath.readthedocs.io/en/stable/docs/tutorials/projects.html) will just work. If it doesn't, you'll notice immediately : the tiles will be shuffled and you'll see only a part of the image instead of the whole one. Unfortunately I was not able to determine why this happens and did not find a way to even predict if a file will or will not work.

In the event you experience this bug, you'll need to export the CZI files to OME-TIFF files from ZEN, then generate tiled pyramidal images with the `pyramid-creator` package that you can find [here](https://github.com/TeamNCMC/pyramid-creator).

## Markdown (.md) files
[Markdown](https://en.wikipedia.org/wiki/Markdown) is a markup language to create formatted text. It is basically a simple text file that could be opened with any text editor software (notepad and the like), but features specific tags to format the text with heading levels, typesetting (**bold**, *itallic*), [links](#markdown-md-files), lists... This very page is actually written in markdown, and the engine that builds it renders the text in a nicely formatted manner.

If you open a .md file with [vscode](https://code.visualstudio.com/) for example, you'll get a magnigying glass on the top right corner to switch to the rendered version of the file.

## TOML (.toml) files
[TOML](https://toml.io/en/), or Tom's Obvious Minimal Language, is a configuration file format (similar to [YAML](https://yaml.org/)). Again, it is basically a simple text file that can be opened with any text editor and is human-readable, but also computer-readable. This means that it is easy for most software and programming language to parse the file to associate a variable (or "key") to a value, thus making it a good file format for configuration. It is used in `cuisto` (see [The configuration files](main-configuration-files.md) page).

The syntax looks like this :
```toml
# a comment, ignored by the computer
key1 = 10  # the key "key1" is mapped to the number 10
key2 = "something"  # "key2" is mapped to the string "something"
key3 = ["something else", 1.10, -25]  # "key3" is mapped to a list with 3 elements
[section]  # we can declare sections
key1 = 5  # this is not "key1", it actually is section.key1
[section.example]  # we can have nested sections
key1 = true  # this is section.example.key1, mapped to the boolean True
```

You can check the full specification of this language [here](https://toml.io/en/v1.0.0).

## CSV (.csv, .tsv) files
CSV (or TSV) stands for Comma-Separated Values (or Tab-Separated Values) and is, once again, a simple text file formatted in a way that allows LibreOffice Calc (or Excel) to open them as a table. Lines of the table are delimited with new lines, and columns are separated with commas (`,`) or tabulations. Those files are easily parsed by programming languages (including Python). QuPath can export annotations and detections measurements in TSV format.

## JSON and GeoJSON files
[JSON](https://www.json.org/json-en.html) is a "data-interchange format". It is used to store data, very much like [toml](#toml-toml-files), but supports more complex data and is more efficient to read and write, but is less human-readable. It is used in `cuisto` to store fibers-like objects coordinates, as they can contain several millions of points (making CSV not usable).

[GeoJson](https://geojson.org/) is a file format used to store geographic data structures, basically objects coordinates with various shapes. It is based on and compatible with JSON, which makes it easy to parse in numerous programming language. It used in QuPath to import and export objects, that can be point, line, polygons...