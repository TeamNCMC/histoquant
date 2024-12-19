# Brain contours
With `cuisto`, it is possible to plot 2D heatmaps on brain contours.

All the detections are projected in a single plane, thus it is up to you to select a relevant data range. It is primarily intended to give a quick, qualitative overview of the spreading of your data.

To do so, it requires the brain regions outlines, stored in a hdf5 file. This can be generated with `brainglobe-atlasapi`. The `generate_atlas_outlines.py` located in `scripts/atlas` will show you how to make such a file, that the `cuisto.display` module can use.

Alternatively it is possible to directly plot density maps without `cuisto`, using `brainglobe-heatmap`. An example is shown [here](demo_notebooks/density_map.ipynb).