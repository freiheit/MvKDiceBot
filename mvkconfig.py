#!.venv/bin/python3
# MvKDiceBot: Discord bot for rolling dice for Mecha Vs Kaiju
# Copyright (C) 2023  Eric Eisenhart
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# https://github.com/freiheit/MvKDiceBot
"""Configuration loading for MvKDiceBot."""

import logging
import os
import warnings
from configparser import ConfigParser

logger = logging.getLogger(__name__)


class ImproperlyConfigured(Exception):
    """Raised when no usable configuration file can be found."""


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser("~")

DEFAULT_CONFIG_PATHS = [
    os.path.join(HOME_DIR, ".mvkdicebot.ini"),
    os.path.join("/etc/mvkdicebot.ini"),
    os.path.join(BASE_DIR, "mvkdicebot.ini"),
    os.path.join("mvkdicebot.ini"),
]


def get_config():
    """Find and parse our config, configuring logging as a side effect."""
    config = ConfigParser()
    config_paths = []

    for path in DEFAULT_CONFIG_PATHS:
        if os.path.isfile(path):
            config_paths.append(path)
            break
    else:
        raise ImproperlyConfigured("No configuration file found.")

    config.read(config_paths)

    debug = config["MAIN"].getint("debug", 0)

    if debug >= 3:
        log_level = logging.DEBUG
    elif debug >= 2:
        log_level = logging.INFO
    elif debug >= 1:
        log_level = logging.WARNING
    else:
        log_level = logging.ERROR

    # Configure the root logger so every module's logger inherits the level.
    logging.basicConfig(level=log_level)
    logging.getLogger().setLevel(log_level)
    warnings.resetwarnings()

    return config


def get_database_path(config):
    """Return the sqlite database path (config ``MAIN.database`` or a default).

    The default lives alongside the code so a plain checkout works out of the box;
    it is gitignored. Used for the per-guild prefix store (prefixstore.py).
    """
    return config["MAIN"].get("database", os.path.join(BASE_DIR, "mvkdicebot.sqlite3"))


def get_primary_guild_ids(config):
    """Return the optional `primary_guilds` config value as a list of guild IDs.

    "Guild" is the Discord API term for a server. The config value is a
    comma/whitespace-separated list; an empty/missing value yields an empty list
    (meaning "sync slash commands globally"). Non-integer tokens are skipped
    with a warning rather than crashing startup.
    """
    raw_guilds = config["MAIN"].get("primary_guilds", "")

    guild_ids = []
    for token in raw_guilds.replace(",", " ").split():
        try:
            guild_ids.append(int(token))
        except ValueError:
            logger.warning("Ignoring invalid primary_guilds entry: %r", token)

    return guild_ids
