# The configuration files

There are three configuration files : `altas_blacklist`, `atlas_fusion` and a modality-specific file, that we'll call `config` in this document. The former two are related to the atlas you're using, the latter is what is used by `histoquant` to know what and how to compute and display things. There is a fourth, optional, file, used to provide some information on a specific experiment, `info`.

The configuration files are in the TOML file format, that are basically text files formatted in a way that is easy to parse in Python. See [here](tips-formats.md#toml-toml-files) for a basic explanation of the syntax.

Most lines of each template file are commented to explain what each parameter do.

## atlas_blacklist.toml
??? abstract "Click to see an example file"
    ```toml title="atlas_blacklist.toml"
    --8<-- "atlas/atlas_blacklist.toml"
    ```
This file is used to filter out specified regions and objects belonging to them.

+ The atlas regions present in the `members` keys will be ignored. Objects whose parents are in here will be ignored as well.
+ In the `[WITH_CHILDS]` section, regions and objects belonging to those regions **and** all descending regions (child regions, as per the altas hierarchy) will be removed.
+ In the `[EXACT]` section, only regions and objects belonging to those **exact** regions are removed. Descendants regions are not taken into account.

## atlas_fusion.toml
??? abstract "Click to see an example file"
    ```toml title="atlas_blacklist.toml"
    --8<-- "atlas/atlas_fusion.toml"
    ```
This file is used to group regions together, to customize the atlas' hierarchy. It is particularly useful to group smalls brain regions that are impossible to register precisely.
Keys `name`, `acronym` and `members` should belong to a `[section]`.

+ `[section]` is just for organizing, the name does not matter but should be unique.
+ `name` should be a human-readable name for your new region.
+ `acronym` is how the region will be refered to. It can be a new acronym, or an existing one.
+ `members` is a list of acronyms of atlas regions that should be part of the new one.

## config.toml
??? abstract "Click to see an example file"
    ```toml title="config_template.toml"
    --8<-- "configs/config_template.toml"
    ```
This file is used to configure `histoquant` behavior. It specifies what to compute, how, and display parameters such as colors associated to each classifications, hemisphere names, distributions bins limits...

!!! warning
    When editing your config.toml file, you're allowed to modify the *keys* **only** in the `[channels]` section.

??? example "Click for a more readable parameters explanation"
    --8<-- "docs/api-config-config.md"

## info.toml
??? abstract "Click to see an example file"
    ```toml title="info_template.toml"
    --8<-- "configs/infos_template.toml"
    ```
This file is used to specify injection sites for each animal and each channel, to display it in distributions.