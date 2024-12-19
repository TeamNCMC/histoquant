"""process module, part of cuisto.

Wraps other functions for a click&play behaviour. Relies on the configuration file.

"""

import os

import pandas as pd
from tqdm import tqdm

from cuisto import compute, io, utils


def process_animal(
    animal: str,
    df_annotations: pd.DataFrame,
    df_detections: pd.DataFrame,
    cfg,
    compute_distributions: bool = True,
) -> tuple[pd.DataFrame, list[pd.DataFrame], pd.DataFrame]:
    """
    Quantify objects for one animal.

    Fetch required files and compute objects' distributions in brain regions, spatial
    distributions and gather Atlas coordinates.

    Parameters
    ----------
    animal : str
        Animal ID.
    df_annotations, df_detections : pd.DataFrame
        DataFrames of QuPath Annotations and Detections.
    cfg : cuisto.Config
        The configuration loaded from TOML configuration file.
    compute_distributions : bool, optional
        If False, do not compute the 1D distributions and return an empty list.Default
        is True.

    Returns
    -------
    df_regions : pandas.DataFrame
        Metrics in brain regions. One entry for each hemisphere of each brain regions.
    df_distribution : list of pandas.DataFrame
        Rostro-caudal distribution, as raw count and probability density function, in
        each axis.
    df_coordinates : pandas.DataFrame
        Atlas coordinates of each points.

    """
    # - Annotations data cleanup
    # filter regions
    df_annotations = utils.filter_df_regions(
        df_annotations, ["Root", "root"], mode="remove", col="Name"
    )
    df_annotations = utils.filter_df_regions(
        df_annotations, cfg.atlas["blacklist"], mode="remove", col="Name"
    )
    # add hemisphere
    df_annotations = utils.add_hemisphere(df_annotations, cfg.hemispheres["names"])
    # remove objects in non-leaf regions
    df_annotations = utils.filter_df_regions(
        df_annotations, cfg.atlas["leaveslist"], mode="keep", col="Name"
    )
    # merge regions
    df_annotations = utils.merge_regions(
        df_annotations, col="Name", fusion_file=cfg.files["fusion"]
    )
    if compute_distributions:
        # - Detections data cleanup
        # remove objects not in selected classifications
        df_detections = utils.filter_df_classifications(
            df_detections, cfg.object_type, mode="keep", col="Classification"
        )
        # remove objects from blacklisted regions and "Root"
        df_detections = utils.filter_df_regions(
            df_detections, cfg.atlas["blacklist"], mode="remove", col="Parent"
        )
        # add hemisphere
        df_detections = utils.add_hemisphere(
            df_detections,
            cfg.hemispheres["names"],
            cfg.atlas["midline"],
            col="Atlas_Z",
            atlas_type=cfg.atlas["type"],
        )
        # add detection channel
        df_detections = utils.add_channel(
            df_detections, cfg.object_type, cfg.channels["names"]
        )
        # convert coordinates to mm
        df_detections[["Atlas_X", "Atlas_Y", "Atlas_Z"]] = df_detections[
            ["Atlas_X", "Atlas_Y", "Atlas_Z"]
        ].divide(1000)
        # convert to sterotaxic coordinates
        if cfg.distributions["stereo"]:
            (
                df_detections["Atlas_AP"],
                df_detections["Atlas_DV"],
                df_detections["Atlas_ML"],
            ) = utils.ccf_to_stereo(
                df_detections["Atlas_X"],
                df_detections["Atlas_Y"],
                df_detections["Atlas_Z"],
            )
        else:
            (
                df_detections["Atlas_AP"],
                df_detections["Atlas_DV"],
                df_detections["Atlas_ML"],
            ) = (
                df_detections["Atlas_X"],
                df_detections["Atlas_Y"],
                df_detections["Atlas_Z"],
            )

    # - Computations
    # get regions distributions
    df_regions = compute.get_regions_metrics(
        df_annotations,
        cfg.object_type,
        cfg.channels["names"],
        cfg.regions["base_measurement"],
        cfg.regions["metrics"],
    )
    colstonorm = [v for v in cfg.regions["metrics"].values() if "relative" not in v]

    # normalize by starter cells
    if cfg.regions["normalize_starter_cells"]:
        df_regions = compute.normalize_starter_cells(
            df_regions, colstonorm, animal, cfg.files["infos"], cfg.channels["names"]
        )

    # get AP, DV, ML distributions in stereotaxic coordinates
    if compute_distributions:
        dfs_distributions = [
            compute.get_distribution(
                df_detections,
                axis,
                cfg.distributions["hue"],
                cfg.distributions["hue_filter"],
                cfg.distributions["common_norm"],
                stereo_lim,
                nbins=nbins,
            )
            for axis, stereo_lim, nbins in zip(
                ["Atlas_AP", "Atlas_DV", "Atlas_ML"],
                [
                    cfg.distributions["ap_lim"],
                    cfg.distributions["dv_lim"],
                    cfg.distributions["ml_lim"],
                ],
                [
                    cfg.distributions["ap_nbins"],
                    cfg.distributions["dv_nbins"],
                    cfg.distributions["dv_nbins"],
                ],
            )
        ]
    else:
        dfs_distributions = []

    # add animal tag to each DataFrame
    df_detections["animal"] = animal
    df_regions["animal"] = animal
    for df in dfs_distributions:
        df["animal"] = animal

    return df_regions, dfs_distributions, df_detections


def process_animals(
    wdir: str,
    animals: list[str] | tuple[str],
    cfg,
    out_fmt: str | None = None,
    compute_distributions: bool = True,
) -> tuple[pd.DataFrame]:
    """
    Get data from all animals and plot.

    Parameters
    ----------
    wdir : str
        Base working directory, containing `animals` folders.
    animals : list-like of str
        List of animals ID.
    cfg: cuisto.Config
        Configuration object.
    out_fmt : {None, "h5", "csv", "tsv", "xslx", "pickle"}
        Output file(s) format, if None, nothing is saved (default).
    compute_distributions : bool, optional
        If False, do not compute the 1D distributions and return an empty list.Default
        is True.


    Returns
    -------
    df_regions : pandas.DataFrame
        Metrics in brain regions. One entry for each hemisphere of each brain regions.
    df_distribution : list of pandas.DataFrame
        Rostro-caudal distribution, as raw count and probability density function, in
        each axis.
    df_coordinates : pandas.DataFrame
        Atlas coordinates of each points.

    """

    # -- Preparation
    df_regions = []
    dfs_distributions = []
    df_coordinates = []

    # -- Processing
    pbar = tqdm(animals)

    for animal in pbar:
        pbar.set_description(f"Processing {animal}")

        # combine all detections and annotations from this animal
        df_annotations = io.cat_csv_dir(
            io.get_measurements_directory(
                wdir, animal, "annotation", cfg.segmentation_tag
            ),
            index_col="Object ID",
            sep="\t",
        )
        if compute_distributions:
            df_detections = io.cat_data_dir(
                io.get_measurements_directory(
                    wdir, animal, "detection", cfg.segmentation_tag
                ),
                cfg.segmentation_tag,
                index_col="Object ID",
                sep="\t",
                hemisphere_names=cfg.hemispheres["names"],
                atlas=cfg.bg_atlas,
            )
        else:
            df_detections = pd.DataFrame()
        
        # get results
        df_reg, dfs_dis, df_coo = process_animal(
            animal,
            df_annotations,
            df_detections,
            cfg,
            compute_distributions=compute_distributions,
        )

        # collect results
        df_regions.append(df_reg)
        dfs_distributions.append(dfs_dis)
        df_coordinates.append(df_coo)

    # concatenate all results
    df_regions = pd.concat(df_regions, ignore_index=True)
    dfs_distributions = [
        pd.concat(dfs_list, ignore_index=True) for dfs_list in zip(*dfs_distributions)
    ]
    df_coordinates = pd.concat(df_coordinates, ignore_index=True)

    # -- Saving
    if out_fmt:
        outdir = os.path.join(wdir, "quantification")
        outfile = f"{cfg.object_type.lower()}_{cfg.atlas["type"]}_{'-'.join(animals)}.{out_fmt}"
        dfs = dict(
            df_regions=df_regions,
            df_coordinates=df_coordinates,
            df_distribution_ap=dfs_distributions[0],
            df_distribution_dv=dfs_distributions[1],
            df_distribution_ml=dfs_distributions[2],
        )
        io.save_dfs(outdir, outfile, dfs)

    return df_regions, dfs_distributions, df_coordinates
