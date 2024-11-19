`object_type` : name of QuPath base classification (eg. without the ": subclass" part)
`segmentation_tag` : type of segmentation, matches directory name, used only in the full pipeline

<h3>atlas</h3>
*Information related to the atlas used*

`name` : brainglobe-atlasapi atlas name  
`type` : "brain" or "cord" (eg. registration done in ABBA or abba_python). This will determine whether to flip Left/Right when determining detections hemisphere based on their coordinates. Also adapts the axes in the 2D heatmaps.  
`midline` : midline Z coordinates (left/right limit) in microns to determine detections hemisphere based on their coordinates.  
`outline_structures` : structures to show an outline of in heatmaps  

<h3>channels</h3>
*Information related to imaging channels*

<h4>names</h4>
*Must contain all classifications derived from "object_type" you want to process. In the form `subclassification name = name to display on the plots`*

`"marker+"` : classification name = name to display  
`"marker-"` : add any number of sub-classification

<h4>colors</h4>
*Must have same keys as "names" keys*, in the form `subclassification name = color`, with color specified as a matplotlib named color, an RGB list or an hex code.

`"marker+"` : classification name = matplotlib color  
`"marker-"` : must have the same entries as "names".

<h3>hemispheres</h3>
*Information related to hemispheres, same structure as channels*

<h4>names</h4>

`Left` : Left = name to display  
`Right` : Right = name to display

<h4>colors</h4>
*Must have same keys as names' keys*

`Left` : ff516e"  # Left = matplotlib color (either #hex, color name or RGB list)  
`Right` : 960010"  # Right = matplotlib color

<h3>distributions</h3>
*Spatial distributions parameters*

`stereo` : use stereotaxic coordinates (as in Paxinos, only for mouse brain CCFv3)  
`ap_lim` : bins limits for anterio-posterior in mm  
`ap_nbins` : number of bins for anterio-posterior  
`dv_lim` : bins limits for dorso-ventral in mm  
`dv_nbins` : number of bins for dorso-ventral  
`ml_lim` : bins limits for medio-lateral in mm  
`ml_nbins` : number of bins for medio-lateral  
`hue` : color curves with this parameter, must be "hemisphere" or "channel"  
`hue_filter` : use only a subset of data

- If hue=hemisphere : it should be a channel name, a list of such or "all"  
- If hue=channel : it should be a hemisphere name or "both"

`common_norm` : use a global normalization (eg. the sum of areas under all curves is 1). Otherwise, normalize each hue individually

<h4>display</h4>
*Display parameters*

`show_injection` : add a patch showing the extent of injection sites. Uses corresponding channel colors. Requires the information TOML configuration file set up
`cmap` : matplotlib color map for 2D heatmaps
`cmap_nbins` : number of bins for 2D heatmaps
`cmap_lim` : color limits for 2D heatmaps

<h3>regions</h3>
*Distributions per regions parameters*

`base_measurement` : the name of the measurement in QuPath to derive others from. Usually "Count" or "Length µm"  
`hue` : color bars with this parameter, must be "hemisphere" or "channel"  
`hue_filter` : use only a subset of data

- If hue=hemisphere : it should be a channel name, a list of such or "all"
- If hue=channel : it should be a hemisphere name or "both"

`hue_mirror` : plot two hue_filter in mirror instead of discarding the others. For example, if hue=channel and hue_filter="both", plots the two hemisphere in mirror.  
`normalize_starter_cells` : normalize non-relative metrics by the number of starter cells

<h4>metrics</h4>
*Names of metrics. The keys are used internally in histoquant as is so should NOT be modified. The values will only chang etheir names in the ouput file*

`"density µm^-2"` : relevant name  
`"density mm^-2"` : relevant name  
`"coverage index"` : relevant name  
`"relative measurement"` : relevant name  
`"relative density"` : relevant name

<h4>display</h4>

`nregions` : number of regions to display (sorted by max.)  
`orientation` : orientation of the bars ("h" or "v")  
`order` : order the regions by "ontology" or by "max". Set to "max" to provide a custom order  
`dodge` : enforce the bar not being stacked  
`log_scale` : use log. scale for metrics

<h5>metrics</h5>
*name of metrics to display*

`"count"` : real_name = display_name, with real_name the "values" in [regions.metrics]
`"density mm^-2"`

<h3>files</h3>
*Full path to information TOML files and atlas outlines for 2D heatmaps.*

`blacklist`  
`fusion`  
`outlines`  
`infos`  