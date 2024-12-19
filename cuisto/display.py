"""display module, part of cuisto.

Contains display functions, essentially wrapping matplotlib and seaborn functions.

"""

import warnings

import h5py
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib import patches

from cuisto import utils


def add_injection_patch(X: list, ax: plt.Axes, **kwargs) -> plt.Axes:
    """
    Add a patch representing the injection sites.

    The patch will span from the minimal coordinate to the maximal.
    If plotted in stereotaxic coordinates, coordinates should be converted beforehand.

    Parameters
    ----------
    X : list
        Coordinates in mm for each animals. Can be empty to not plot anything.
    ax : Axes
        Handle to axes where to add the patch.
    **kwargs : passed to Axes.axvspan

    Returns
    -------
    ax : Axes
        Handle to updated Axes.

    """
    # plot patch
    if len(X) > 0:
        ax.axvspan(min(X), max(X), **kwargs)

    return ax


def add_data_coverage(
    df: pd.DataFrame, ax: plt.Axes, colors: list | str | None = None, **kwargs
) -> plt.Axes:
    """
    Add lines below the plot to represent data coverage.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with `X_min` and `X_max` on rows for each animals (on columns).
    ax : Axes
        Handle to axes where to add the patch.
    colors : list or str or None, optional
        Colors for the patches, as a RGB list or hex list. Should be the same size as
        the number of patches to plot, eg. the number of columns in `df`. If None,
        default seaborn colors are used. If only one element, used for each animal.
    **kwargs : passed to patches.Rectangle()

    Returns
    -------
    ax : Axes
        Handle to updated axes.

    """
    # get colors
    ncolumns = len(df.columns)
    if not colors:
        colors = sns.color_palette(n_colors=ncolumns)
    elif isinstance(colors, str) or (isinstance(colors, list) & (len(colors) == 3)):
        colors = [colors] * ncolumns
    elif len(colors) != ncolumns:
        warnings.warn(f"Wrong number of colors ({len(colors)}), using default colors.")
        colors = sns.color_palette(n_colors=ncolumns)

    # get patch height depending on current axis limits
    ymin, ymax = ax.get_ylim()
    height = (ymax - ymin) * 0.02

    for animal, color in zip(df.columns, colors):
        # get patch coordinates
        ymin, ymax = ax.get_ylim()
        ylength = ymax - ymin
        ybottom = ymin - 0.02 * ylength
        xleft = df.loc["X_min", animal]
        xright = df.loc["X_max", animal]

        # plot patch
        ax.add_patch(
            patches.Rectangle(
                (xleft, ybottom),
                xright - xleft,
                height,
                label=animal,
                color=color,
                **kwargs,
            )
        )

        ax.autoscale(tight=True)  # set new axes limits

    ax.autoscale()  # reset scale

    return ax


def draw_structure_outline(
    view: str = "sagittal",
    structures: list[str] = ["root"],
    outline_file: str = "",
    ax: plt.Axes | None = None,
    microns: bool = False,
    **kwargs,
) -> plt.Axes:
    """
    Plot brain regions outlines in given projection.

    This requires a file containing the structures outlines.

    Parameters
    ----------
    view : str
        Projection, "sagittal", "coronal" or "top". Default is "sagittal".
    structures : list[str]
        List of structures acronyms whose outlines will be drawn. Default is ["root"].
    outline_file : str
        Full path the outlines HDF5 file.
    ax : plt.Axes or None, optional
        Axes where to plot the outlines. If None, get current axes (the default).
    microns : bool, optional
        If False (default), converts the coordinates in mm.
    **kwargs : passed to pyplot.plot()

    Returns
    -------
    ax : plt.Axes

    """
    # get axes
    if not ax:
        ax = plt.gca()

    # get units
    if microns:
        conv = 1
    else:
        conv = 1 / 1000

    with h5py.File(outline_file) as f:
        if view == "sagittal":
            for structure in structures:
                dsets = f["sagittal"][structure]

                for dset in dsets.values():
                    ax.plot(dset[:, 0] * conv, dset[:, 1] * conv, **kwargs)

        if view == "coronal":
            for structure in structures:
                dsets = f["coronal"][structure]

                for dset in dsets.values():
                    ax.plot(dset[:, 0] * conv, dset[:, 1] * conv, **kwargs)

        if view == "top":
            for structure in structures:
                dsets = f["top"][structure]

                for dset in dsets.values():
                    ax.plot(dset[:, 0] * conv, dset[:, 1] * conv, **kwargs)

    return ax


def nice_bar_plot(
    df: pd.DataFrame,
    x: str = "",
    y: list[str] = [""],
    hue: str = "",
    ylabel: list[str] = [""],
    orient="h",
    nx: None | int = None,
    ordering: None | list[str] | str = None,
    names_list: None | list = None,
    hue_mirror: bool = False,
    log_scale: bool = False,
    bar_kws: dict = {},
    pts_kws: dict = {},
) -> list[plt.Axes]:
    """
    Nice bar plot of per-region objects distribution.

    This is used for objects distribution across brain regions. Shows the `y` metric
    (count, aeral density, cumulated length...) in each `x` categories (brain regions).
    `orient` controls wether the bars are shown horizontally (default) or vertically.
    Input `df` must have an additional "hemisphere" column. All `y` are plotted in the
    same figure as different subplots. `nx` controls the number of displayed regions.

    Parameters
    ----------
    df : pandas.DataFrame
    x, y, hue : str
        Key in `df`.
    ylabel : list of str
        Y axis labels.
    orient : "h" or "v", optional
        "h" for horizontal bars (default) or "v" for vertical bars.
    nx : None or int, optional
        Number of `x` to show in the plot. Default is None (no limit).
    ordering : None or list[str] or "max", optional
        Sorted list of acronyms. Data will be sorted follwowing this order, if "max",
        sorted by descending values, if None, not sorted (default).
    names_list : list or None, optional
        List of names to display. If None (default), takes the most prominent overall
        ones.
    hue_mirror : bool, optional
        If there are 2 groups, plot in mirror. Default is False.
    log_scale : bool, optional
        Set the metrics in log scale. Default is False.
    bar_kws : dict
        Passed to seaborn.barplot().
    pts_kws : dict
        Passed to seaborn.stripplot().

    Returns
    -------
    figs : list
        List of figures.

    """
    figs = []
    # loop for each features
    for yi, ylabeli in zip(y, ylabel):
        # prepare data
        # get nx first most prominent regions
        if not names_list:
            names_list_plt = (
                df.groupby(["Name"])[yi].mean().sort_values(ascending=False).index[0:nx]
            )
        else:
            names_list_plt = names_list
        dfplt = df[df["Name"].isin(names_list_plt)]  # limit to those regions
        # limit hierarchy list if provided
        if isinstance(ordering, list):
            order = [el for el in ordering if el in names_list_plt]
        elif ordering == "max":
            order = names_list_plt
        else:
            order = None

        # reorder keys depending on orientation and create axes
        if orient == "h":
            xp = yi
            yp = x
            if hue_mirror:
                nrows = 1
                ncols = 2
                sharex = None
                sharey = "all"
            else:
                nrows = 1
                ncols = 1
                sharex = None
                sharey = None
        elif orient == "v":
            xp = x
            yp = yi
            if hue_mirror:
                nrows = 2
                ncols = 1
                sharex = "all"
                sharey = None
            else:
                nrows = 1
                ncols = 1
                sharex = None
                sharey = None
        fig, axs = plt.subplots(nrows=nrows, ncols=ncols, sharex=sharex, sharey=sharey)

        if hue_mirror:
            # two graphs
            ax1, ax2 = axs
            # determine what will be mirrored
            if hue == "channel":
                hue_filter = "hemisphere"
            elif hue == "hemisphere":
                hue_filter = "channel"
            # select the two types (should be left/right or two channels)
            hue_filters = dfplt[hue_filter].unique()[0:2]
            hue_filters.sort()  # make sure it will be always in the same order

            # plot
            for filt, ax in zip(hue_filters, [ax1, ax2]):
                dfplt2 = dfplt[dfplt[hue_filter] == filt]
                ax = sns.barplot(
                    dfplt2,
                    x=xp,
                    y=yp,
                    hue=hue,
                    estimator="mean",
                    errorbar="se",
                    orient=orient,
                    order=order,
                    ax=ax,
                    **bar_kws,
                )
                # add points
                ax = sns.stripplot(
                    dfplt2, x=xp, y=yp, hue=hue, legend=False, ax=ax, **pts_kws
                )

                # cosmetics
                if orient == "h":
                    ax.set_title(f"{hue_filter}: {filt}")
                    ax.set_ylabel(None)
                    ax.set_ylim((nx + 0.5, -0.5))
                    if log_scale:
                        ax.set_xscale("log")

                elif orient == "v":
                    if ax == ax1:
                        # top title
                        ax1.set_title(f"{hue_filter}: {filt}")
                        ax.set_xlabel(None)
                    elif ax == ax2:
                        # use xlabel as bottom title
                        ax2.set_xlabel(
                            f"{hue_filter}: {filt}", fontsize=ax1.title.get_fontsize()
                        )
                    ax.set_xlim((-0.5, nx + 0.5))
                    if log_scale:
                        ax.set_yscale("log")

                    for label in ax.get_xticklabels():
                        label.set_verticalalignment("center")
                        label.set_horizontalalignment("center")

            # tune axes cosmetics
            if orient == "h":
                ax1.set_xlabel(ylabeli)
                ax2.set_xlabel(ylabeli)
                ax1.set_xlim(
                    ax1.get_xlim()[0], max((ax1.get_xlim()[1], ax2.get_xlim()[1]))
                )
                ax2.set_xlim(
                    ax2.get_xlim()[0], max((ax1.get_xlim()[1], ax2.get_xlim()[1]))
                )
                ax1.invert_xaxis()
                sns.despine(ax=ax1, left=True, top=True, right=False, bottom=False)
                sns.despine(ax=ax2, left=False, top=True, right=True, bottom=False)
                ax1.yaxis.tick_right()
                ax1.tick_params(axis="y", pad=20)
                for label in ax1.get_yticklabels():
                    label.set_verticalalignment("center")
                    label.set_horizontalalignment("center")
            elif orient == "v":
                ax2.set_ylabel(ylabeli)
                ax1.set_ylim(
                    ax1.get_ylim()[0], max((ax1.get_ylim()[1], ax2.get_ylim()[1]))
                )
                ax2.set_ylim(
                    ax2.get_ylim()[0], max((ax1.get_ylim()[1], ax2.get_ylim()[1]))
                )
                ax2.invert_yaxis()
                sns.despine(ax=ax1, left=False, top=True, right=True, bottom=False)
                sns.despine(ax=ax2, left=False, top=False, right=True, bottom=True)
                for label in ax2.get_xticklabels():
                    label.set_verticalalignment("center")
                    label.set_horizontalalignment("center")
                ax2.tick_params(axis="x", labelrotation=90, pad=20)

        else:
            # one graph
            ax = axs
            # plot
            ax = sns.barplot(
                dfplt,
                x=xp,
                y=yp,
                hue=hue,
                estimator="mean",
                errorbar="se",
                orient=orient,
                order=order,
                ax=ax,
                **bar_kws,
            )
            # add points
            ax = sns.stripplot(
                dfplt, x=xp, y=yp, hue=hue, legend=False, ax=ax, **pts_kws
            )

            # cosmetics
            if orient == "h":
                ax.set_xlabel(ylabeli)
                ax.set_ylabel(None)
                ax.set_ylim((nx + 0.5, -0.5))
                if log_scale:
                    ax.set_xscale("log")
            elif orient == "v":
                ax.set_xlabel(None)
                ax.set_ylabel(ylabeli)
                ax.set_xlim((-0.5, nx + 0.5))
                if log_scale:
                    ax.set_yscale("log")

        fig.tight_layout(pad=0)
        figs.append(fig)

    return figs


def nice_distribution_plot(
    df: pd.DataFrame,
    x: str = "",
    y: str = "",
    hue: str | None = None,
    xlabel: str = "",
    ylabel: str = "",
    injections_sites: dict = {},
    channel_colors: dict = {},
    channel_names: dict = {},
    ax: plt.Axes | None = None,
    **kwargs,
) -> plt.Axes:
    """
    Nice plot of 1D distribution of objects.

    Parameters
    ----------
    df : pandas.DataFrame
    x, y : str
        Keys in `df`.
    hue : str or None, optional
        Key in `df`. If None, no hue is used.
    xlabel, ylabel : str
        X and Y axes labels.
    injections_sites : dict, optional
        List of injection sites 1D coordinates in a dict with the channel name as key.
        If empty, injection site is not plotted (default).
    channel_colors : dict, optional
        Required if injections_sites is not empty, dict mapping channel names to a
        color.
    channel_names : dict, optional
        Required if injections_sites is not empty, dict mapping channel names to a
        display name.
    ax : Axes or None, optional
        Axes in which to plot the figure, if None, a new figure is created (default).
    **kwargs : passed to seaborn.lineplot()

    Returns
    -------
    ax : matplotlib axes
        Handle to axes.

    """
    if not ax:
        # create figure
        _, ax = plt.subplots(figsize=(10, 6))

    ax = sns.lineplot(
        df,
        x=x,
        y=y,
        hue=hue,
        estimator="mean",
        errorbar="se",
        ax=ax,
        **kwargs,
    )

    for channel in injections_sites.keys():
        ax = add_injection_patch(
            injections_sites[channel],
            ax,
            color=channel_colors[channel],
            edgecolor=None,
            alpha=0.25,
            label=channel_names[channel] + ": inj. site",
        )

    ax.legend()
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    return ax


def nice_joint_plot(
    df: pd.DataFrame,
    x: str = "",
    y: str = "",
    xlabel: str = "",
    ylabel: str = "",
    invertx: bool = False,
    inverty: bool = False,
    outline_kws: dict = {},
    ax: plt.Axes | None = None,
    **kwargs,
) -> plt.Figure:
    """
    Joint distribution.

    Used to display a 2D heatmap of objects. This is more qualitative than quantitative,
    for display purposes.

    Parameters
    ----------
    df : pandas.DataFrame
    x, y : str
        Keys in `df`.
    xlabel, ylabel : str
        Label of x and y axes.
    invertx, inverty : bool, optional
        Whether to inverse the x or y axes. Default is False for both.
    outline_kws : dict
        Passed to draw_structure_outline().
    ax : plt.Axes or None, optional
        Axes to plot in. If None, draws in current axes (default).
    **kwargs
        Passed to seaborn.histplot.

    Returns
    -------
    ax : plt.Axes

    """
    if not ax:
        ax = plt.gca()

    # plot outline
    draw_structure_outline(ax=ax, **outline_kws)

    # plot joint distribution
    sns.histplot(
        df,
        x=x,
        y=y,
        ax=ax,
        **kwargs,
    )

    # adjust axes
    if invertx:
        ax.invert_xaxis()
    if inverty:
        ax.invert_yaxis()

    # labels
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    return ax


def nice_heatmap(
    df: pd.DataFrame,
    animals: tuple[str] | list[str],
    x: str = "",
    y: str = "",
    xlabel: str = "",
    ylabel: str = "",
    invertx: bool = False,
    inverty: bool = False,
    **kwargs,
) -> list[plt.Axes] | plt.Axes:
    """
    Nice plots of 2D distribution of boutons as a heatmap per animal.

    Parameters
    ----------
    df : pandas.DataFrame
    animals : list-like of str
        List of animals.
    x, y : str
        Keys in `df`.
    xlabel, ylabel : str
        Labels of x and y axes.
    invertx, inverty : bool, optional
        Wether to inverse the x or y axes. Default is False.
    **kwargs : passed to seaborn.histplot()

    Returns
    -------
    ax : Axes or list of Axes
        Handle to axes.

    """

    # 2D distribution, per animal
    _, axs = plt.subplots(len(animals), 1, sharex="all")

    for animal, ax in zip(animals, axs):
        ax = sns.histplot(
            df[df["animal"] == animal],
            x=x,
            y=y,
            ax=ax,
            **kwargs,
        )
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(animal)

        if inverty:
            ax.invert_yaxis()

    if invertx:
        axs[-1].invert_xaxis()  # only once since all x axes are shared

    return axs


def plot_regions(df: pd.DataFrame, cfg, **kwargs):
    """
    Wraps nice_bar_plot().
    """
    # get regions order
    if cfg.regions["display"]["order"] == "ontology":
        regions_order = [d["acronym"] for d in cfg.bg_atlas.structures_list]
    elif cfg.regions["display"]["order"] == "max":
        regions_order = "max"
    else:
        regions_order = None

    # determine metrics to be plotted and color palette based on hue
    metrics = [*cfg.regions["display"]["metrics"].keys()]
    hue = cfg.regions["hue"]
    palette = cfg.get_hue_palette("regions")

    # select data
    dfplt = utils.select_hemisphere_channel(
        df, hue, cfg.regions["hue_filter"], cfg.regions["hue_mirror"]
    )

    # prepare options
    bar_kws = dict(
        err_kws={"linewidth": 1.5},
        dodge=cfg.regions["display"]["dodge"],
        palette=palette,
    )
    pts_kws = dict(
        size=4,
        edgecolor="auto",
        linewidth=0.75,
        dodge=cfg.regions["display"]["dodge"],
        palette=palette,
    )
    # draw
    figs = nice_bar_plot(
        dfplt,
        x="Name",
        y=metrics,
        hue=hue,
        ylabel=[*cfg.regions["display"]["metrics"].values()],
        orient=cfg.regions["display"]["orientation"],
        nx=cfg.regions["display"]["nregions"],
        ordering=regions_order,
        hue_mirror=cfg.regions["hue_mirror"],
        log_scale=cfg.regions["display"]["log_scale"],
        bar_kws=bar_kws,
        pts_kws=pts_kws,
        **kwargs,
    )

    return figs


def plot_1D_distributions(
    dfs_distributions: list[pd.DataFrame],
    cfg,
    df_coordinates: pd.DataFrame = None,
):
    """
    Wraps nice_distribution_plot().
    """
    # prepare figures
    fig, axs_dist = plt.subplots(1, 3, sharey=True, figsize=(13, 6))
    xlabels = [
        "Rostro-caudal position (mm)",
        "Dorso-ventral position (mm)",
        "Medio-lateral position (mm)",
    ]

    # get animals
    animals = []
    for df in dfs_distributions:
        animals.extend(df["animal"].unique())
    animals = set(animals)

    # get injection sites
    if cfg.distributions["display"]["show_injection"]:
        injection_sites = cfg.get_injection_sites(animals)
    else:
        injection_sites = {k: {} for k in range(3)}

    # get color palette based on hue
    hue = cfg.distributions["hue"]
    palette = cfg.get_hue_palette("distributions")

    # loop through each axis
    for df_dist, ax_dist, xlabel, inj_sites in zip(
        dfs_distributions, axs_dist, xlabels, injection_sites.values()
    ):
        # select data
        if cfg.distributions["hue"] == "hemisphere":
            dfplt = df_dist[df_dist["hemisphere"] != "both"]
        elif cfg.distributions["hue"] == "channel":
            dfplt = df_dist[df_dist["channel"] != "all"]

        # plot
        ax_dist = nice_distribution_plot(
            dfplt,
            x="bins",
            y="distribution",
            hue=hue,
            xlabel=xlabel,
            ylabel="normalized distribution",
            injections_sites=inj_sites,
            channel_colors=cfg.channels["colors"],
            channel_names=cfg.channels["names"],
            linewidth=2,
            palette=palette,
            ax=ax_dist,
        )

        # add data coverage
        if ("Atlas_AP" in df_dist["axis"].unique()) & (df_coordinates is not None):
            df_coverage = utils.get_data_coverage(df_coordinates)
            ax_dist = add_data_coverage(df_coverage, ax_dist, edgecolor=None, alpha=0.5)
            ax_dist.legend()
        else:
            ax_dist.legend().remove()

    # - Distributions, per animal
    if len(animals) > 1:
        _, axs_dist = plt.subplots(1, 3, sharey=True)

        # loop through each axis
        for df_dist, ax_dist, xlabel, inj_sites in zip(
            dfs_distributions, axs_dist, xlabels, injection_sites.values()
        ):
            # select data
            df_dist_plot = df_dist[df_dist["hemisphere"] == "both"]

            # plot
            ax_dist = nice_distribution_plot(
                df_dist_plot,
                x="bins",
                y="distribution",
                hue="animal",
                xlabel=xlabel,
                ylabel="normalized distribution",
                injections_sites=inj_sites,
                channel_colors=cfg.channels["colors"],
                channel_names=cfg.channels["names"],
                linewidth=2,
                ax=ax_dist,
            )

    return fig


def plot_2D_distributions(df: pd.DataFrame, cfg):
    """
    Wraps nice_joint_plot().
    """
    # -- 2D heatmap, all animals pooled
    # prepare figure
    fig_heatmap = plt.figure(figsize=(12, 9))

    ax_sag = fig_heatmap.add_subplot(2, 2, 1)
    ax_cor = fig_heatmap.add_subplot(2, 2, 2, sharey=ax_sag)
    ax_top = fig_heatmap.add_subplot(2, 2, 3, sharex=ax_sag)
    ax_cbar = fig_heatmap.add_subplot(2, 2, 4, box_aspect=15)

    # prepare options
    map_options = dict(
        bins=cfg.distributions["display"]["cmap_nbins"],
        cmap=cfg.distributions["display"]["cmap"],
        rasterized=True,
        thresh=10,
        stat="count",
        vmin=cfg.distributions["display"]["cmap_lim"][0],
        vmax=cfg.distributions["display"]["cmap_lim"][1],
    )
    outline_kws = dict(
        structures=cfg.atlas["outline_structures"],
        outline_file=cfg.files["outlines"],
        linewidth=1.5,
        color="k",
    )
    cbar_kws = dict(label="count")

    # determine which axes are going to be inverted
    if cfg.atlas["type"] == "brain":
        cor_invertx = True
        cor_inverty = False
        top_invertx = True
        top_inverty = False
    elif cfg.atlas["type"] == "cord":
        cor_invertx = False
        cor_inverty = False
        top_invertx = True
        top_inverty = True

    # - sagittal
    # no need to invert axes because they are shared with the two other views
    outline_kws["view"] = "sagittal"
    nice_joint_plot(
        df,
        x="Atlas_X",
        y="Atlas_Y",
        xlabel="Rostro-caudal (mm)",
        ylabel="Dorso-ventral (mm)",
        outline_kws=outline_kws,
        ax=ax_sag,
        **map_options,
    )

    # - coronal
    outline_kws["view"] = "coronal"
    nice_joint_plot(
        df,
        x="Atlas_Z",
        y="Atlas_Y",
        xlabel="Medio-lateral (mm)",
        ylabel="Dorso-ventral (mm)",
        invertx=cor_invertx,
        inverty=cor_inverty,
        outline_kws=outline_kws,
        ax=ax_cor,
        **map_options,
    )
    ax_cor.invert_yaxis()

    # - top
    outline_kws["view"] = "top"
    nice_joint_plot(
        df,
        x="Atlas_X",
        y="Atlas_Z",
        xlabel="Rostro-caudal (mm)",
        ylabel="Medio-lateral (mm)",
        invertx=top_invertx,
        inverty=top_inverty,
        outline_kws=outline_kws,
        ax=ax_top,
        cbar=True,
        cbar_ax=ax_cbar,
        cbar_kws=cbar_kws,
        **map_options,
    )
    fig_heatmap.suptitle("sagittal, coronal and top-view projections")

    # -- 2D heatmap per animals
    # get animals
    animals = df["animal"].unique()
    if len(animals) > 1:
        # Rostro-caudal, dorso-ventral (sagittal)
        _ = nice_heatmap(
            df,
            animals,
            x="Atlas_X",
            y="Atlas_Y",
            xlabel="Rostro-caudal (mm)",
            ylabel="Dorso-ventral (mm)",
            invertx=True,
            inverty=True,
            cmap="OrRd",
            rasterized=True,
            cbar=True,
        )

        # Medio-lateral, dorso-ventral (coronal)
        _ = nice_heatmap(
            df,
            animals,
            x="Atlas_Z",
            y="Atlas_Y",
            xlabel="Medio-lateral (mm)",
            ylabel="Dorso-ventral (mm)",
            inverty=True,
            invertx=True,
            cmap="OrRd",
            rasterized=True,
        )

    return fig_heatmap
