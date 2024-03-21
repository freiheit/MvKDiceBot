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
"""MvKDiceBot: Discord bot for rolling dice for Mecha Vs Kaiju"""

import logging
import os
import warnings
from configparser import ConfigParser
import discord
from discord.ext import commands
import mvkroller

__version__ = "1.0.0"
DESCRIPTION = """A dice rolling bot for MvK
"""

intents = discord.Intents.default()
# intents.members = True
# intents.messages = True
intents.message_content = True  # pylint: disable=assigning-non-slot

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("?"),
    description=DESCRIPTION,
    intents=intents,
)


@bot.event
async def on_ready():
    """Log when we start up"""
    # pylint: disable=logging-fstring-interpolation
    logger.warning(f"Logged in as {bot.user} (ID {bot.user.id})")


@bot.hybrid_command(
    aliases=["r", "R", "roll", "rolldice", "diceroll"]
)  # pylint: disable=no-member
async def mvkroll(ctx, *, dicestr: str):
    """Rolls NdN format pool of dice and does MvK rules math for you.

    Example: '?roll 1d20 2d10 d8 2d6'

    Add 'advantage' to discard lowest d20.
    Add 'disadvantage' to discard highest d20.
    Example: '?roll 2d20 2d10 advantage'
    Example: '?roll 2d20 2d10 disadvantage'

    Ignores anything extra it doesn't understand.
    """
    try:
        response = mvkroller.mvkroll(dicestr)
        await ctx.reply(response)
    except mvkroller.RollError as exc:
        await ctx.reply(exc.getMessage())
        raise


@bot.hybrid_command(
    aliases=["p", "P", "pr", "PR", "justroll", "justdice", "plain"]
)  # pylint: disable=no-member
async def plainroll(ctx, *, dicestr: str):
    """Just rolls NdN format pool of dice.

    Example: '?roll 1d20 2d10 d8 2d6'

    Ignores anything extra it doesn't understand.
    """
    try:
        response = mvkroller.plainroll(dicestr)
        await ctx.reply(response)
    except mvkroller.RollError as exc:
        await ctx.reply(exc.getMessage())
        raise


class ImproperlyConfigured(Exception):
    """Boring Exception Class"""

    # pylint: disable=unnecessary-pass
    pass


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.path.expanduser("~")

DEFAULT_CONFIG_PATHS = [
    os.path.join(HOME_DIR, ".mvkdicebot.ini"),
    os.path.join("/etc/mvkdicebot.ini"),
    os.path.join(BASE_DIR, "mvkdicebot.ini"),
    os.path.join("mvkdicebot.ini"),
]


def get_config():
    """Find and parse our config"""
    # pylint: disable=redefined-outer-name
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

    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    warnings.resetwarnings()
    logger.addHandler(logging.StreamHandler())

    return config, logger


config, logger = get_config()

bot.run(
    token=config["MAIN"].get("authtoken"),
    reconnect=True,
    log_level=logging.WARNING,
)
