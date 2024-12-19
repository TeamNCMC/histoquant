"""utils module, part of cuisto.

Contains utilities functions.

"""

import tomllib
import warnings

import numpy as np
import pandas as pd
from brainglobe_atlasapi import BrainGlobeAtlas


def get_starter_cells(animal: str, channel: str, info_file: str) -> int:
    """
    Get the number of starter cells associated with animal.

    Parameters
    ----------
    animal : str
        Animal ID.
    channel : str
        Channel ID.
    info_file : str
        Path to TOML info file.

    Returns
    -------
    n_starters : int
        Number of starter cells.

    """
    with open(info_file, "rb") as fid:
        info = tomllib.load(fid)

    return info[animal][channel]["starter_cells"]


def get_injection_site(
    animal: str, info_file: str, channel: str, stereo: bool = False
) -> tuple:
    """
    Get the injection site coordinates associated with animal.

    Parameters
    ----------
    animal : str
        Animal ID.
    info_file : str
        Path to TOML info file.
    channel : str
        Channel ID as in the TOML file.
    stereo : bool, optional
        Wether to convert coordinates in stereotaxis coordinates. Default is False.

    Returns
    -------
    x, y, z : floats
        Injection site coordinates.

    """
    with open(info_file, "rb") as fid:
        info = tomllib.load(fid)

    if channel in info[animal]:
        x, y, z = info[animal][channel]["injection_site"]
        if stereo:
            x, y, z = ccf_to_stereo(x, y, z)
    else:
        x, y, z = None, None, None

    return x, y, z


def get_mapping_fusion(fusion_file: str) -> dict:
    """
    Get mapping dictionnary between input brain regions and new regions defined in
    `atlas_fusion.toml` file.

    The returned dictionnary can be used in DataFrame.replace().

    Parameters
    ----------
    fusion_file : str
        Path to the TOML file with the merging rules.

    Returns
    -------
    m : dict
        Mapping as {old: new}.

    """
    with open(fusion_file, "rb") as fid:
        df = pd.DataFrame.from_dict(tomllib.load(fid), orient="index").set_index(
            "acronym"
        )

    return (
        df.drop(columns="name")["members"]
        .explode()
        .reset_index()
        .set_index("members")
        .to_dict()["acronym"]
    )


def get_blacklist(file: str, atlas: BrainGlobeAtlas) -> list:
    """
    Build a list of regions to exclude from file.

    File must be a TOML with [WITH_CHILDS] and [EXACT] sections.

    Parameters
    ----------
    file : str
        Full path the atlas_blacklist.toml file.
    atlas : BrainGlobeAtlas
        Atlas to extract regions from.

    Returns
    -------
    black_list : list
        Full list of acronyms to discard.

    """
    with open(file, "rb") as fid:
        content = tomllib.load(fid)

    blacklist = []  # init. the list

    # add regions and their descendants
    for region in content["WITH_CHILDS"]["members"]:
        blacklist.extend(
            [
                atlas.structures[id]["acronym"]
                for id in atlas.structures.tree.expand_tree(
                    atlas.structures[region]["id"]
                )
            ]
        )

    # add regions specified exactly (no descendants)
    blacklist.extend(content["EXACT"]["members"])

    return blacklist


def merge_regions(df: pd.DataFrame, col: str, fusion_file: str) -> pd.DataFrame:
    """
    Merge brain regions following rules in the `fusion_file.toml` file.

    Apply this merging on `col` of the input DataFrame. `col` whose value is found in
    the `members` sections in the file will be changed to the new acronym.

    Parameters
    ----------
    df : pandas.DataFrame
    col : str
        Column of `df` on which to apply the mapping.
    fusion_file : str
        Path to the toml file with the merging rules.

    Returns
    -------
    df : pandas.DataFrame
        Same DataFrame with regions renamed.

    """
    df[col] = df[col].replace(get_mapping_fusion(fusion_file))

    return df


def get_leaves_list(atlas: BrainGlobeAtlas) -> list:
    """
    Get the list of leaf brain regions.

    Leaf brain regions are defined as regions without childs, eg. regions that are at
    the bottom of the hiearchy.

    Parameters
    ----------
    atlas : BrainGlobeAtlas
        Atlas to extract regions from.

    Returns
    -------
    leaves_list : list
        Acronyms of leaf brain regions.

    """
    leaves_list = []
    for region in atlas.structures_list:
        if atlas.structures.tree[region["id"]].is_leaf():
            leaves_list.append(region["acronym"])

    return leaves_list


def ccf_to_stereo(
    x_ccf: float | np.ndarray, y_ccf: float | np.ndarray, z_ccf: float | np.ndarray = 0
) -> tuple:
    """
    Convert X, Y, Z coordinates in CCFv3 to stereotaxis coordinates (as in
    Paxinos-Franklin atlas).

    Coordinates are shifted, rotated and squeezed, see (1) for more info. Input must be
    in mm.
    `x_ccf` corresponds to the anterio-posterior (rostro-caudal) axis.
    `y_ccf` corresponds to the dorso-ventral axis.
    `z_ccf` corresponds to the medio-lateral axis (left-right) axis.

    Warning : it is a rough estimation.

    (1) https://community.brain-map.org/t/how-to-transform-ccf-x-y-z-coordinates-into-stereotactic-coordinates/1858

    Parameters
    ----------
    x_ccf, y_ccf : floats or np.ndarray
        Coordinates in CCFv3 space in mm.
    z_ccf : float or np.ndarray, optional
        Coordinate in CCFv3 space in mm. Default is 0.

    Returns
    -------
    ap, dv, ml : floats or np.ndarray
        Stereotaxic coordinates in mm.

    """
    # Center CCF on Bregma
    xstereo = -(x_ccf - 5.40)  # anterio-posterior coordinate (rostro-caudal)
    ystereo = y_ccf - 0.44  # dorso-ventral coordinate
    ml = z_ccf - 5.70  # medio-lateral coordinate (left-right)

    # Rotate CCF of 5°
    angle = np.deg2rad(5)
    ap = xstereo * np.cos(angle) - ystereo * np.sin(angle)
    dv = xstereo * np.sin(angle) + ystereo * np.cos(angle)

    # Squeeze the dorso-ventral axis by 94.34%
    dv *= 0.9434

    return ap, dv, ml


def get_df_kind(df: pd.DataFrame) -> str:
    """
    Get DataFrame kind, eg. Annotations or Detections.

    It is based on reading the Object Type of the first entry, so the DataFrame must
    have only one kind of object.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    kind : str
        "detection" or "annotation".

    """
    return df["Object type"].iloc[0].lower()


def add_hemisphere(
    df: pd.DataFrame,
    hemisphere_names: dict,
    midline: float = 5700,
    col: str = "Atlas_Z",
    atlas_type: str = "brain",
) -> pd.DataFrame:
    """
    Add hemisphere (left/right) as a measurement for detections or annotations.

    The hemisphere is read in the "Classification" column for annotations. The latter
    needs to be in the form "Right: Name" or "Left: Name". For detections, the input
    `col` of `df` is compared to `midline` to assess if the object belong to the left or
    right hemispheres.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with detections or annotations measurements.
    hemisphere_names : dict
        Map between "Left" and "Right" to something else.
    midline : float
        Used only for "detections" `df`. Corresponds to the brain midline in microns,
        should be 5700 for CCFv3 and 1610 for spinal cord.
    col : str, optional
        Name of the column containing the Z coordinate (medio-lateral) in microns.
        Default is "Atlas_Z".
    atlas_type : {"brain", "cord"}, optional
        Type of atlas used for registration. Required because the brain atlas is swapped
        between left and right while the spinal cord atlas is not. Default is "brain".

    Returns
    -------
    df : pandas.DataFrame
        The same DataFrame with a new "hemisphere" column

    """
    # check if there is something to do
    if "hemisphere" in df.columns:
        return df

    # get kind of DataFrame
    kind = get_df_kind(df)

    if kind == "detection":
        # use midline
        if atlas_type == "brain":
            # brain atlas : beyond midline, it's left
            df.loc[df[col] >= midline, "hemisphere"] = hemisphere_names["Left"]
            df.loc[df[col] < midline, "hemisphere"] = hemisphere_names["Right"]
        elif atlas_type == "cord":
            # cord atlas : below midline, it's left
            df.loc[df[col] <= midline, "hemisphere"] = hemisphere_names["Left"]
            df.loc[df[col] > midline, "hemisphere"] = hemisphere_names["Right"]

    elif kind == "annotation":
        # use Classification name -- this does not depend on atlas type
        df["hemisphere"] = [name.split(":")[0] for name in df["Classification"]]
        df["hemisphere"] = df["hemisphere"].map(hemisphere_names)

    return df


def add_channel(
    df: pd.DataFrame, object_type: str, channel_names: dict
) -> pd.DataFrame:
    """
    Add channel as a measurement for detections DataFrame.

    The channel is read from the Classification column, the latter having to be
    formatted as "object_type: channel".

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with detections measurements.
    object_type : str
        Object type (primary classification).
    channel_names : dict
        Map between original channel names to something else.

    Returns
    -------
    pd.DataFrame
        Same DataFrame with a "channel" column.

    """
    # check if there is something to do
    if "channel" in df.columns:
        return df

    kind = get_df_kind(df)
    if kind == "annotation":
        warnings.warn("Annotation DataFrame not supported.")
        return df

    # add channel, from {class_name: channel} classification
    df["channel"] = (
        df["Classification"].str.replace(object_type + ": ", "").map(channel_names)
    )

    return df


def add_brain_region(
    df: pd.DataFrame, atlas: BrainGlobeAtlas, col="Parent"
) -> pd.DataFrame:
    """
    Add brain region to a DataFrame with `Atlas_X`, `Atlas_Y` and `Atlas_Z` columns.

    This uses Brainglobe Atlas API to query the atlas. It does not use the
    structure_from_coords() method, instead it manually converts the coordinates in
    stack indices, then get the corresponding annotation id and query the corresponding
    acronym -- because brainglobe-atlasapi is not vectorized at all.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with atlas coordinates in microns.
    atlas : BrainGlobeAtlas
    col : str, optional
        Column in which to put the regions acronyms. Default is "Parent".

    Returns
    -------
    df : pd.DataFrame
        Same DataFrame with a new "Parent" column.

    """
    df_in = df.copy()

    res = atlas.resolution  # microns <-> pixels conversion
    lims = atlas.shape_um  # out of brain

    # set out-of-brain objects at 0 so we get "root" as their parent
    df_in.loc[(df_in["Atlas_X"] >= lims[0]) | (df_in["Atlas_X"] < 0), "Atlas_X"] = 0
    df_in.loc[(df_in["Atlas_Y"] >= lims[1]) | (df_in["Atlas_Y"] < 0), "Atlas_Y"] = 0
    df_in.loc[(df_in["Atlas_Z"] >= lims[2]) | (df_in["Atlas_Z"] < 0), "Atlas_Z"] = 0

    # build the multi index, in pixels and integers
    ixyz = (
        df_in["Atlas_X"].divide(res[0]).astype(int),
        df_in["Atlas_Y"].divide(res[1]).astype(int),
        df_in["Atlas_Z"].divide(res[2]).astype(int),
    )
    # convert i, j, k indices in raveled indices
    linear_indices = np.ravel_multi_index(ixyz, dims=atlas.annotation.shape)
    # get the structure id from the annotation stack
    idlist = atlas.annotation.ravel()[linear_indices]
    # replace 0 which does not exist to 997 (root)
    idlist[idlist == 0] = 997

    # query the corresponding acronyms
    lookup = atlas.lookup_df.set_index("id")
    df.loc[:, col] = lookup.loc[idlist, "acronym"].values

    return df


def filter_df_classifications(
    df: pd.DataFrame, filter_list: list | tuple | str, mode="keep", col="Classification"
) -> pd.DataFrame:
    """
    Filter a DataFrame whether specified `col` column entries contain elements in
    `filter_list`. Case insensitive.

    If `mode` is "keep", keep entries only if their `col` in is in the list (default).
    If `mode` is "remove", remove entries if their `col` is in the list.

    Parameters
    ----------
    df : pd.DataFrame
    filter_list : list | tuple | str
        List of words that should be present to trigger the filter.
    mode : "keep" or "remove", optional
        Keep or remove entries from the list. Default is "keep".
    col : str, optional
        Key in `df`. Default is "Classification".

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.

    """
    # check input
    if isinstance(filter_list, str):
        filter_list = [filter_list]  # make sure it is a list

    if col not in df.columns:
        # might be because of 'Classification' instead of 'classification'
        col = col.capitalize()
        if col not in df.columns:
            raise KeyError(f"{col} not in DataFrame.")

    pattern = "|".join(f".*{s}.*" for s in filter_list)

    if mode == "keep":
        df_return = df[df[col].str.contains(pattern, case=False, regex=True)]
    elif mode == "remove":
        df_return = df[~df[col].str.contains(pattern, case=False, regex=True)]

    # check
    if len(df_return) == 0:
        raise ValueError(
            (
                f"Filtering '{col}' with {filter_list} resulted in an"
                + " empty DataFrame, check your config file."
            )
        )
    return df_return


def filter_df_regions(
    df: pd.DataFrame, filter_list: list | tuple, mode="keep", col="Parent"
) -> pd.DataFrame:
    """
    Filters entries in `df` based on wether their `col` is in `filter_list` or not.

    If `mode` is "keep", keep entries only if their `col` in is in the list (default).
    If `mode` is "remove", remove entries if their `col` is in the list.

    Parameters
    ----------
    df : pandas.DataFrame
    filter_list : list-like
        List of regions to keep or remove from the DataFrame.
    mode : "keep" or "remove", optional
        Keep or remove entries from the list. Default is "keep".
    col : str, optional
        Key in `df`. Default is "Parent".

    Returns
    -------
    df : pandas.DataFrame
        Filtered DataFrame.

    """

    if mode == "keep":
        return df[df[col].isin(filter_list)]
    if mode == "remove":
        return df[~df[col].isin(filter_list)]


def get_data_coverage(df: pd.DataFrame, col="Atlas_AP", by="animal") -> pd.DataFrame:
    """
    Get min and max in `col` for each `by`.

    Used to get data coverage for each animal to plot in distributions.

    Parameters
    ----------
    df : pd.DataFrame
        _description_
    col : str, optional
        Key in `df`, default is "Atlas_X".
    by : str, optional
        Key in `df` , default is "animal".

    Returns
    -------
    pd.DataFrame
        min and max of `col` for each `by`, named "X_min", and "X_max".

    """
    df_group = df.groupby([by])
    return pd.DataFrame(
        [
            df_group[col].min(),
            df_group[col].max(),
        ],
        index=["X_min", "X_max"],
    )


def renormalize_per_key(df: pd.DataFrame, by: str, on: str):
    """
    Renormalize `on` column by its sum for each `by`.

    Use case : relative density is computed for both hemispheres, so if one wants to
    plot only one hemisphere, the sum of the bars corresponding to one channel (`by`)
    should be 1. So :
    >>> df = df[df["hemisphere"] == "Ipsi."]
    >>> df = renormalize_per_key(df, "channel", "relative density")
    Then, the sum of "relative density" for each "channel" equals 1.

    Parameters
    ----------
    df : pd.DataFrame
    by : str
        Key in `df`. `df` is normalized for each `by`.
    on : str
        Key in `df`. Measurement to be normalized.

    Returns
    -------
    df : pd.DataFrame
        Same DataFrame with normalized `on` column.

    """
    norm = df.groupby(by)[on].sum()
    bys = df[by].unique()
    for key in bys:
        df.loc[df[by] == key, on] = df.loc[df[by] == key, on].divide(norm[key])

    return df


def select_hemisphere_channel(
    df: pd.DataFrame, hue: str, hue_filter: str, hue_mirror: bool
) -> pd.DataFrame:
    """
    Select relevant data given hue and filters.

    Returns the DataFrame with only things to be used.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to filter.
    hue : {"hemisphere", "channel"}
        hue that will be used in seaborn plots.
    hue_filter : str
        Selected data.
    hue_mirror : bool
        Instead of keeping only hue_filter values, they will be plotted in mirror.

    Returns
    -------
    dfplt : pd.DataFrame
        DataFrame to be used in plots.

    """
    dfplt = df.copy()

    if hue == "hemisphere":
        # hue_filter is used to select channels
        # keep only left and right hemispheres, not "both"
        dfplt = dfplt[dfplt["hemisphere"] != "both"]
        if hue_filter == "all":
            hue_filter = dfplt["channel"].unique()
        elif not isinstance(hue_filter, (list, tuple)):
            # it is allowed to select several channels so handle lists
            hue_filter = [hue_filter]
        dfplt = dfplt[dfplt["channel"].isin(hue_filter)]
    elif hue == "channel":
        # hue_filter is used to select hemispheres
        # it can only be left, right, both or empty
        if hue_filter == "both":
            # handle if it's a coordinates DataFrame which doesn't have "both"
            if "both" not in dfplt["hemisphere"].unique():
                # keep both hemispheres, don't do anything
                pass
            else:
                if hue_mirror:
                    # we need to keep both hemispheres to plot them in mirror
                    dfplt = dfplt[dfplt["hemisphere"] != "both"]
                else:
                    # we keep the metrics computed in both hemispheres
                    dfplt = dfplt[dfplt["hemisphere"] == "both"]
        else:
            # hue_filter should correspond to an hemisphere name
            dfplt = dfplt[dfplt["hemisphere"] == hue_filter]
    else:
        # not handled. Just return the DataFrame without filtering, maybe it'll make
        # sense.
        warnings.warn(f"{hue} should be 'channel' or 'hemisphere'.")

    # check result
    if len(dfplt) == 0:
        warnings.warn(
            f"hue={hue} and hue_filter={hue_filter} resulted in an empty subset."
        )

    return dfplt
