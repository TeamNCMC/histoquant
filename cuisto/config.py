"""config module, part of cuisto.

Contains the Config class.

"""

import tomllib
import warnings

from brainglobe_atlasapi import BrainGlobeAtlas
from cuisto import utils


class Config:
    """
    The configuration class.

    Reads input configuration file and provides its constant.

    Parameters
    ----------
    config_file : str
        Full path to the configuration file to load.

    Returns
    -------
    cfg : Config object.

    """

    def __init__(self, config_file):
        """Constructor."""
        with open(config_file, "rb") as fid:
            cfg = tomllib.load(fid)

            for key in cfg:
                setattr(self, key, cfg[key])

        self.config_file = config_file
        self.bg_atlas = BrainGlobeAtlas(self.atlas["name"], check_latest=False)
        self.get_blacklist()
        self.get_leaves_list()

    def get_blacklist(self):
        """Wraps cuisto.utils.get_blacklist."""

        self.atlas["blacklist"] = utils.get_blacklist(
            self.files["blacklist"], self.bg_atlas
        )

    def get_leaves_list(self):
        """Wraps utils.get_leaves_list."""

        self.atlas["leaveslist"] = utils.get_leaves_list(self.bg_atlas)

    def get_injection_sites(self, animals: list[str]) -> dict:
        """
        Get list of injection sites coordinates for each animals, for each channels.

        Parameters
        ----------
        animals : list of str
            List of animals.

        Returns
        -------
        injection_sites : dict
            {"x": {channel0: [x]}, "y": {channel1: [y]}}

        """
        injection_sites = {
            axis: {channel: [] for channel in self.channels["names"].keys()}
            for axis in ["x", "y", "z"]
        }

        for animal in animals:
            for channel in self.channels["names"].keys():
                injx, injy, injz = utils.get_injection_site(
                    animal,
                    self.files["infos"],
                    channel,
                    stereo=self.distributions["stereo"],
                )
                if injx is not None:
                    injection_sites["x"][channel].append(injx)
                if injy is not None:
                    injection_sites["y"][channel].append(injy)
                if injz is not None:
                    injection_sites["z"][channel].append(injz)

        return injection_sites

    def get_hue_palette(self, mode: str) -> dict:
        """
        Get color palette given hue.

        Maps hue to colors in channels or hemispheres.

        Parameters
        ----------
        mode : {"hemisphere", "channel"}

        Returns
        -------
        palette : dict
            Maps a hue level to a color, usable in seaborn.

        """
        params = getattr(self, mode)

        if params["hue"] == "channel":
            # replace channels by their new names
            palette = {
                self.channels["names"][k]: v for k, v in self.channels["colors"].items()
            }
        elif params["hue"] == "hemisphere":
            # replace hemispheres by their new names
            palette = {
                self.hemispheres["names"][k]: v
                for k, v in self.hemispheres["colors"].items()
            }
        else:
            palette = None
            warnings.warn(f"hue={self.regions["display"]["hue"]} not supported.")

        return palette
