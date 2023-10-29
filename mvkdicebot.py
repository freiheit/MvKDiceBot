#!/usr/bin/env python3
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

import asyncio
import discord
import logging
import random

from configparser import ConfigParser
from discord.ext import commands

__version__ = "0.0.1"
description = '''A dice rolling bot for MvK
'''

intents = discord.Intents.default()

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

DEFAULT_CONFIG_PATHS = [
    os.path.join(HOME_DIR, ".mvkdicebot.ini"),
    os.path.join("/etc/mvkdicebot.ini"),
    os.path.join(BASE_DIR, "mvkdicebot.ini"),
    os.path.join("mvkdicebot.ini"),
]

def get_config():
    config = ConfigParser()
    config_paths = []

    if args.config:
        config_paths = [args.config]
    else:
        for path in DEFAULT_CONFIG_PATHS:
            if os.path.isfile(path):
                config_paths.append(path)
                break
        else:
            raise ImproperlyConfigured("No configuration file found.")

        for path in DEFAULT_AUTH_CONFIG_PATHS:
            if os.path.isfile(path):
                config_paths.append(path)
                break

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

    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    warnings.resetwarnings()

    return config, logger

config, logger = get_config()

