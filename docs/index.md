# Introduction

!!! info
    The documentation is under construction.

`histoquant` is a Python package aiming at **quant**ifying **histo**logical data.

After [ABBA](https://abba-documentation.readthedocs.io/en/latest/) registration of 2D histological slices and [QuPath](https://qupath.readthedocs.io/en/stable/) objects' detection, `histoquant` is used to :

+ compute metrics, such as objects density in each brain regions,
+ compute objects distributions in three three axes (rostro-caudal, dorso-ventral and medio-lateral),
+ compute averages and sem across animals,
+ displaying all the above.

This documentation contains `histoquant` installation instructions, ABBA installation instructions, guides to prepare images for the pipeline, detect objects with QuPath, register 2D slices on a 3D atlas with ABBA, along with examples.

In theory, `histoquant` should work with any measurements table with the [required columns](guide-prepare-qupath.md#qupath-requirements), but has been designed with ABBA and QuPath in mind.

Due to the IT environment of the laboratory, this documentation is very Windows-oriented but most of it should be applicable to Linux and MacOS as well by slightly adapting terminal commands.

![Histological slices analysis pipeline](images/hq-pipeline.svg)

## Documentation navigation
The documentation outline is on the left panel, you can click on items to browse it. In each page, you'll get the table of contents on the right panel.

## Useful external resources
+ Project repository : [https://github.com/TeamNCMC/histoquant](https://github.com/TeamNCMC/histoquant)
+ QuPath documentation : [https://qupath.readthedocs.io/en/stable/](https://qupath.readthedocs.io/en/stable/)
+ Aligning Big Brain and Atlases (ABBA) documentation : [https://abba-documentation.readthedocs.io/en/latest/](https://abba-documentation.readthedocs.io/en/latest/)
+ Brainglobe : [https://brainglobe.info/](https://brainglobe.info/)
+ BraiAn, a similar but published and way more feature-packed project : [https://silvalab.codeberg.page/BraiAn/](https://silvalab.codeberg.page/BraiAn/)
+ Image.sc community forum : [https://forum.image.sc/](https://forum.image.sc/)
+ *Introduction to Bioimage Analysis*, an interactive book written by QuPath's creator : [https://bioimagebook.github.io/index.html](https://bioimagebook.github.io/index.html)

## Credits
`histoquant` has been primarly developped by [Guillaume Le Goc](https://legoc.fr) in [Julien Bouvier's lab](https://www.bouvier-lab.com/) at [NeuroPSI](https://neuropsi.cnrs.fr/).

The documentation itself is built with [MkDocs](https://www.mkdocs.org/) using the [Material theme](https://squidfunk.github.io/mkdocs-material/).