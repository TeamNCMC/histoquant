"""compute module, part of cuisto.

Contains actual computation functions.

"""

import numpy as np
import pandas as pd

from cuisto.utils import get_starter_cells, select_hemisphere_channel


def get_regions_metrics(
    df_annotations: pd.DataFrame,
    object_type: str,
    channel_names: dict,
    meas_base_name: str,
    metrics_names: dict,
) -> pd.DataFrame:
    """
    Get a new DataFrame with cumulated axons segments length in each brain regions.

    This is the quantification per brain regions for fibers-like objects, eg. axons. The
    returned DataFrame has columns "cum. length µm", "cum. length mm", "density µm^-1",
    "density mm^-1", "coverage index".

    Parameters
    ----------
    df_annotations : pandas.DataFrame
        DataFrame with an entry for each brain regions, with columns "Area µm^2",
        "Name", "hemisphere", and "{object_type: channel} Length µm".
    object_type : str
        Object type (primary classification).
    channel_names : dict
        Map between original channel names to something else.
    meas_base_name : str
    metrics_names : dict

    Returns
    -------
    df_regions : pandas.DataFrame
        DataFrame with brain regions name, area and metrics.

    """
    # get columns names
    cols = df_annotations.columns
    # get columns with fibers lengths
    cols_colors = cols[
        cols.str.startswith(object_type) & cols.str.endswith(meas_base_name)
    ]
    # select relevant data
    cols_to_select = pd.Index(["Name", "hemisphere", "Area µm^2"]).append(cols_colors)
    # sum lengths and areas of each brain regions
    df_regions = (
        df_annotations[cols_to_select]
        .groupby(["Name", "hemisphere"])
        .sum()
        .reset_index()
    )

    # get measurement for both hemispheres (sum)
    df_both = df_annotations[cols_to_select].groupby(["Name"]).sum().reset_index()
    df_both["hemisphere"] = "both"
    df_regions = (
        pd.concat([df_regions, df_both], ignore_index=True)
        .sort_values(by="Name")
        .reset_index()
        .drop(columns="index")
    )

    # rename measurement columns to lower case
    df_regions = df_regions.rename(
        columns={
            k: k.replace(meas_base_name, meas_base_name.lower()) for k in cols_colors
        }
    )

    # update names
    meas_base_name = meas_base_name.lower()
    cols = df_regions.columns
    cols_colors = cols[
        cols.str.startswith(object_type) & cols.str.endswith(meas_base_name)
    ]

    # convert area in mm^2
    df_regions["Area mm^2"] = df_regions["Area µm^2"] / 1e6

    # prepare metrics
    if "µm" in meas_base_name:
        # fibers : convert to mm
        cols_to_convert = pd.Index([col for col in cols_colors if "µm" in col])
        df_regions[cols_to_convert.str.replace("µm", "mm")] = (
            df_regions[cols_to_convert] / 1000
        )
        metrics = [meas_base_name, meas_base_name.replace("µm", "mm")]
    else:
        # objects : count
        metrics = [meas_base_name]

    # density = measurement / area
    metric = metrics_names["density µm^-2"]
    df_regions[cols_colors.str.replace(meas_base_name, metric)] = df_regions[
        cols_colors
    ].divide(df_regions["Area µm^2"], axis=0)
    metrics.append(metric)
    metric = metrics_names["density mm^-2"]
    df_regions[cols_colors.str.replace(meas_base_name, metric)] = df_regions[
        cols_colors
    ].divide(df_regions["Area mm^2"], axis=0)
    metrics.append(metric)

    # coverage index = measurement² / area
    metric = metrics_names["coverage index"]
    df_regions[cols_colors.str.replace(meas_base_name, metric)] = (
        df_regions[cols_colors].pow(2).divide(df_regions["Area µm^2"], axis=0)
    )
    metrics.append(metric)

    # prepare relative metrics columns
    metric = metrics_names["relative measurement"]
    cols_rel_meas = cols_colors.str.replace(meas_base_name, metric)
    df_regions[cols_rel_meas] = np.nan
    metrics.append(metric)
    metric = metrics_names["relative density"]
    cols_dens = cols_colors.str.replace(meas_base_name, metrics_names["density mm^-2"])
    cols_rel_dens = cols_colors.str.replace(meas_base_name, metric)
    df_regions[cols_rel_dens] = np.nan
    metrics.append(metric)
    # relative metrics should be defined within each hemispheres (left, right, both)
    for hemisphere in df_regions["hemisphere"].unique():
        row_indexer = df_regions["hemisphere"] == hemisphere

        # relative measurement = measurement / total measurement
        df_regions.loc[row_indexer, cols_rel_meas] = (
            df_regions.loc[row_indexer, cols_colors]
            .divide(df_regions.loc[row_indexer, cols_colors].sum())
            .to_numpy()
        )

        # relative density = density / total density
        df_regions.loc[row_indexer, cols_rel_dens] = (
            df_regions.loc[
                row_indexer,
                cols_dens,
            ]
            .divide(df_regions.loc[row_indexer, cols_dens].sum())
            .to_numpy()
        )

    # collect channel names
    channels = (
        cols_colors.str.replace(object_type + ": ", "")
        .str.replace(" " + meas_base_name, "")
        .values.tolist()
    )
    # collect measurements columns names
    cols_metrics = df_regions.columns.difference(
        pd.Index(["Name", "hemisphere", "Area µm^2", "Area mm^2"])
    )
    for metric in metrics:
        cols_to_cat = [f"{object_type}: {cn} {metric}" for cn in channels]
        # make sure it's part of available metrics
        if not set(cols_to_cat) <= set(cols_metrics):
            raise ValueError(f"{cols_to_cat} not in DataFrame.")
        # group all colors in the same colors
        df_regions[metric] = df_regions[cols_to_cat].values.tolist()
        # remove original data
        df_regions = df_regions.drop(columns=cols_to_cat)

    # add a color tag, given their names in the configuration file
    df_regions["channel"] = len(df_regions) * [[channel_names[k] for k in channels]]
    metrics.append("channel")

    # explode the dataframe so that each color has an entry
    df_regions = df_regions.explode(metrics)

    return df_regions


def get_distribution(
    df: pd.DataFrame,
    col: str,
    hue: str,
    hue_filter: dict,
    per_commonnorm: bool,
    binlim: tuple | list,
    nbins=100,
) -> pd.DataFrame:
    """
    Computes distribution of objects.

    A global distribution using only `col` is computed, then it computes a distribution
    distinguishing values in the `hue` column. For the latter, it is possible to use a
    subset of the data ony, based on another column using `hue_filter`. This another
    column is determined with `hue`, if the latter is "hemisphere", then `hue_filter` is
    used in the "channel" color and vice-versa.
    `per_commonnorm` controls how they are normalized, either as a whole (True) or
    independantly (False).

    Use cases :
    (1) single-channel, two hemispheres : `col=x`, `hue=hemisphere`, `hue_filter=""`,
    `per_commonorm=True`. Computes a distribution for each hemisphere, the sum of the
    area of both is equal to 1.
    (2) three-channels, one hemisphere : `col=x`, hue=`channel`,
    `hue_filter="Ipsi.", per_commonnorm=False`. Computes a distribution for each channel
    only for points in the ipsilateral hemisphere. Each curve will have an area of 1.

    Parameters
    ----------
    df : pandas.DataFrame
    col : str
        Key in `df`, used to compute the distributions.
    hue : str
        Key in `df`. Criterion for additional distributions.
    hue_filter : str
        Further filtering for "per" distribution.
        - hue = channel : value is the name of one of the hemisphere
        - hue = hemisphere : value can be the name of a channel, a list of such or "all"
    per_commonnorm : bool
        Use common normalization for all hues (per argument).
    binlim : list or tuple
        First bin left edge and last bin right edge.
    nbins : int, optional
        Number of bins. Default is 100.

    Returns
    -------
    df_distribution : pandas.DataFrame
        DataFrame with `bins`, `distribution`, `count` and their per-hemisphere or
        per-channel variants.

    """

    # - Preparation
    bin_edges = np.linspace(*binlim, nbins + 1)  # create bins
    df_distribution = []  # prepare list of distributions

    # - Both hemispheres, all channels
    # get raw count per bins (histogram)
    count, bin_edges = np.histogram(df[col], bin_edges)
    # get normalized count (pdf)
    distribution, _ = np.histogram(df[col], bin_edges, density=True)
    # get bin centers rather than edges to plot them
    bin_centers = bin_edges[:-1] + np.diff(bin_edges) / 2

    # make a DataFrame out of that
    df_distribution.append(
        pd.DataFrame(
            {
                "bins": bin_centers,
                "distribution": distribution,
                "count": count,
                "hemisphere": "both",
                "channel": "all",
                "axis": col,  # keep track of what col. was used
            }
        )
    )

    # - Per additional criterion
    # select data
    df_sub = select_hemisphere_channel(df, hue, hue_filter, False)
    hue_values = df[hue].unique()  # get grouping values
    # total number of datapoints in the subset used for additional distribution
    length_total = len(df_sub)

    for value in hue_values:
        # select part and coordinates
        df_part = df_sub.loc[df_sub[hue] == value, col]

        # get raw count per bins (histogram)
        count, bin_edges = np.histogram(df_part, bin_edges)
        # get normalized count (pdf)
        distribution, _ = np.histogram(df_part, bin_edges, density=True)

        if per_commonnorm:
            # re-normalize so that the sum of areas of all sub-parts is 1
            length_part = len(df_part)  # number of datapoints in that hemisphere
            distribution *= length_part / length_total

        # get bin centers rather than edges to plot them
        bin_centers = bin_edges[:-1] + np.diff(bin_edges) / 2

        # make a DataFrame out of that
        df_distribution.append(
            pd.DataFrame(
                {
                    "bins": bin_centers,
                    "distribution": distribution,
                    "count": count,
                    hue: value,
                    "channel" if hue == "hemisphere" else "hemisphere": hue_filter,
                    "axis": col,  # keep track of what col. was used
                }
            )
        )

    return pd.concat(df_distribution)


def normalize_starter_cells(
    df: pd.DataFrame, cols: list[str], animal: str, info_file: str, channel_names: dict
) -> pd.DataFrame:
    """
    Normalize data by the number of starter cells.

    Parameters
    ----------
    df : pd.DataFrame
        Contains the data to be normalized.
    cols : list-like
        Columns to divide by the number of starter cells.
    animal : str
        Animal ID to parse the number of starter cells.
    info_file : str
        Full path to the TOML file with informations.
    channel_names : dict
        Map between original channel names to something else.

    Returns
    -------
    pd.DataFrame
        Same `df` with normalized count.

    """
    for channel in df["channel"].unique():
        # inverse mapping channel colors : names
        reverse_channels = {v: k for k, v in channel_names.items()}
        nstarters = get_starter_cells(animal, reverse_channels[channel], info_file)

        for col in cols:
            df.loc[df["channel"] == channel, col] = (
                df.loc[df["channel"] == channel, col] / nstarters
            )

    return df
