"""io module, part of cuisto.

Contains loading and saving functions.

"""

import os

from brainglobe_atlasapi import BrainGlobeAtlas
from cuisto import utils
import orjson
import pandas as pd

JSON_KW = ["fibers", "axons", "fiber", "axon"]
CSV_KW = ["synapto", "synaptophysin", "syngfp", "boutons", "points"] + [
    "cells",
    "polygon",
    "polygons",
    "polygon",
    "cell",
]


def get_measurements_directory(wdir, animal: str, kind: str, segtype: str) -> str:
    """
    Get the directory with detections or annotations measurements for given animal ID.

    Parameters
    ----------
    wdir : str
        Base working directory.
    animal : str
        Animal ID.
    kind : str
        "annotation" or "detection".
    segtype : str
        Type of segmentation, eg. "synaptophysin".

    Returns
    -------
    directory : str
        Path to detections or annotations directory.

    """
    bdir = os.path.join(wdir, animal, animal.lower() + "_segmentation", segtype)

    if (kind == "detection") or (kind == "detections"):
        return os.path.join(bdir, "detections")
    elif (kind == "annotation") or (kind == "annotations"):
        return os.path.join(bdir, "annotations")
    else:
        raise ValueError(
            f"kind = '{kind}' not supported. Choose 'detection' or 'annotation'."
        )


def check_empty_file(filename: str, threshold: int = 1) -> bool:
    """
    Checks if a file is empty.

    Empty is defined as a file whose number of lines is lower than or equal to
    `threshold` (to allow for headers).

    Parameters
    ----------
    filename : str
        Full path to the file to check.
    threshold : int, optional
        If number of lines is lower than or equal to this value, it is considered as
        empty. Default is 1.

    Returns
    -------
    empty : bool
        True if the file is empty as defined above.

    """
    with open(filename, "rb") as fid:
        nlines = sum(1 for _ in fid)

    if nlines <= threshold:
        return True
    else:
        return False


def cat_csv_dir(directory, **kwargs) -> pd.DataFrame:
    """
    Scans a directory for csv files and concatenate them into a single DataFrame.

    Parameters
    ----------
    directory : str
        Path to the directory to scan.
    **kwargs : passed to pandas.read_csv()

    Returns
    -------
    df : pandas.DataFrame
        All CSV files concatenated in a single DataFrame.

    """
    return pd.concat(
        pd.read_csv(
            os.path.join(directory, filename),
            **kwargs,
        )
        for filename in os.listdir(directory)
        if (filename.endswith(".csv"))
        and not check_empty_file(os.path.join(directory, filename), threshold=1)
    )


def cat_json_dir(
    directory: str, hemisphere_names: dict, atlas: BrainGlobeAtlas
) -> pd.DataFrame:
    """
    Scans a directory for json files and concatenate them in a single DataFrame.

    The json files must be generated with 'workflow_import_export.groovy" from a QuPath
    project.

    Parameters
    ----------
    directory : str
        Path to the directory to scan.
    hemisphere_names : dict
        Maps between hemisphere names in the json files ("Right" and "Left") to
        something else (eg. "Ipsi." and "Contra.").
    atlas : BrainGlobeAtlas
        Atlas to read regions from.

    Returns
    -------
    df : pd.DataFrame
        All JSON files concatenated in a single DataFrame.

    """
    # list files
    files_list = [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if (filename.endswith(".json"))
    ]

    data = []  # prepare list of DataFrame
    for filename in files_list:
        with open(filename, "rb") as fid:
            df = pd.DataFrame.from_dict(
                orjson.loads(fid.read())["paths"], orient="index"
            )
            df["Image"] = os.path.basename(filename).split("_detections")[0]
            data.append(df)

    df = (
        pd.concat(data)
        .explode(
            ["x", "y", "z", "hemisphere"]
        )  # get an entry for each point of segments
        .reset_index()
        .rename(
            columns=dict(
                x="Atlas_X",
                y="Atlas_Y",
                z="Atlas_Z",
                index="Object ID",
                classification="Classification",
            )
        )
        .set_index("Object ID")
    )

    # change hemisphere names
    df["hemisphere"] = df["hemisphere"].map(hemisphere_names)

    # add object type
    df["Object type"] = "Detection"

    # add brain regions
    df = utils.add_brain_region(df, atlas, col="Parent")

    return df


def cat_data_dir(directory: str, segtype: str, **kwargs) -> pd.DataFrame:
    """
    Wraps either cat_csv_dir() or cat_json_dir() depending on `segtype`.

    Parameters
    ----------
    directory : str
        Path to the directory to scan.
    segtype : str
        "synaptophysin" or "fibers".
    **kwargs : passed to cat_csv_dir() or cat_json_dir().

    Returns
    -------
    df : pd.DataFrame
        All files concatenated in a single DataFrame.

    """
    if segtype in CSV_KW:
        # remove kwargs for json
        kwargs.pop("hemisphere_names", None)
        kwargs.pop("atlas", None)
        return cat_csv_dir(directory, **kwargs)
    elif segtype in JSON_KW:
        kwargs = {k: kwargs[k] for k in ["hemisphere_names", "atlas"] if k in kwargs}
        return cat_json_dir(directory, **kwargs)
    else:
        raise ValueError(
            f"'{segtype}' not supported, unable to determine if CSV or JSON."
        )


def save_dfs(out_dir: str, filename, dfs: dict):
    """
    Save DataFrames to file.

    File format is inferred from file name extension.

    Parameters
    ----------
    out_dir : str
        Output directory.
    filename : _type_
        File name.
    dfs : dict
        DataFrames to save, as {identifier: df}. If HDF5 or xlsx, all df are saved in
        the same file, otherwise identifier is appended to the file name.

    """
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    basename, ext = os.path.splitext(filename)
    if ext in [".h5", ".hdf", ".hdf5"]:
        path = os.path.join(out_dir, filename)
        for identifier, df in dfs.items():
            df.to_hdf(path, key=identifier)
    elif ext == ".xlsx":
        for identifier, df in dfs.items():
            df.to_excel(path, sheet_name=identifier)
    else:
        for identifier, df in dfs.items():
            path = os.path.join(out_dir, f"{basename}_{identifier}{ext}")
            if ext in [".pickle", ".pkl"]:
                df.to_pickle(path)
            elif ext == ".csv":
                df.to_csv(path)
            elif ext == ".tsv":
                df.to_csv(path, sep="\t")
            else:
                raise ValueError(f"{filename} has an unsupported extension.")


def load_dfs(
    filepath: str,
    fmt: str,
    identifiers: list[str] = [
        "df_regions",
        "df_coordinates",
        "df_distribution_ap",
        "df_distribution_dv",
        "df_distribution_ml",
    ],
):
    """
    Load DataFrames from file.

    If `fmt` is "h5" ("xslx"), identifiers are interpreted as h5 group identifier (sheet
    name, respectively).
    If `fmt` is "pickle", "csv" or "tsv", identifiers are appended to `filename`.
    Path to the file can't have a dot (".") in it.

    Parameters
    ----------
    filepath : str
        Full path to the file(s), without extension.
    fmt : {"h5", "csv", "pickle", "xlsx"}
        File(s) format.
    identifiers : list of str, optional
        List of identifiers to load from files. Defaults to the ones saved in
        cuisto.process.process_animals().

    Returns
    -------
    All requested DataFrames.

    """
    # ensure filename without extension
    base_path = os.path.splitext(filepath)[0]
    full_path = base_path + "." + fmt

    res = []
    if (fmt == "h5") or (fmt == "hdf") or (fmt == "hdf5"):
        for identifier in identifiers:
            res.append(pd.read_hdf(full_path, identifier))
    elif fmt == "xlsx":
        for identifier in identifiers:
            res.append(pd.read_excel(full_path, sheet_name=identifier))
    else:
        for identifier in identifiers:
            id_path = f"{base_path}_{identifier}.{fmt}"
            if (fmt == "pickle") or (fmt == "pkl"):
                res.append(pd.read_pickle(id_path))
            elif fmt == "csv":
                res.append(pd.read_csv(id_path))
            elif fmt == "tsv":
                res.append(pd.read_csv(id_path, sep="\t"))
            else:
                raise ValueError(f"{fmt} is not supported.")

    return res
