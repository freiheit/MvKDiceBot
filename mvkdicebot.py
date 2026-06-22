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
from discord import app_commands
from discord.ext import commands

import mvkroller

__version__ = "1.0.0"
DESCRIPTION = """A dice rolling bot for MvK
"""

# Module-level logger; level/handlers are configured in get_config().
logger = logging.getLogger(__name__)

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
async def setup_hook():
    """Register application (slash) commands with Discord on startup.

    The commands are declared as hybrid commands, so discord.py already has the
    slash-command definitions in the command tree; syncing tells Discord about
    them. This is a global sync, which can take up to ~1 hour to propagate the
    first time.
    """
    try:
        synced = await bot.tree.sync()
        # pylint: disable=logging-not-lazy
        logger.warning("Synced %d application command(s)", len(synced))
    except Exception:  # pylint: disable=broad-except
        logger.exception("Failed to sync application commands")


@bot.event
async def on_ready():
    """Log when we start up"""
    # pylint: disable=logging-fstring-interpolation
    logger.warning(f"Logged in as {bot.user} (ID {bot.user.id})")


@bot.hybrid_command(aliases=["r", "R", "roll", "rolldice", "diceroll"])  # pylint: disable=no-member
@app_commands.describe(
    dicestr="Dice to roll, e.g. '1d20 2d10 d8 2d6'. Add 'advantage'/'disadvantage' for the d20."
)
async def mvkroll(ctx, *, dicestr: str):
    """Rolls NdN format pool of dice and does MvK rules math for you.

    Usable as the '?roll'/'@MvkDiceBot roll' text command or the '/mvkroll'
    slash command.

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
    aliases=["p", "d", "D", "P", "pr", "PR", "justroll", "justdice", "plain", "dice"]
)  # pylint: disable=no-member
@app_commands.describe(
    dicestr="Dice to roll plus +N/-N modifiers, e.g. '1d20 2d10 d8 +5'"
)
async def plainroll(ctx, *, dicestr: str):
    """Rolls NdN format pool of dice. Only accepts d20, d12, d10, d8, d6 and d4 dice.

    Usable as the '?p'/'@MvkDiceBot plainroll' text command or the '/plainroll'
    slash command.

    For single d20, may call out likely special things like 20=crit, 1=fail, even and odd.

    Accepts multiple +N and -N modifiers.

    Prints a total of all the dice and the modifiers.

    Example: '?justroll 1d20 2d10 d8 2d6 d6' (note: will work out that it's 3d6)
    Example: '?p 1d20 +5 +2' (note: will add 7 to whatever is rolled)

    Ignores anything extra it doesn't understand.  Doesn't handle
    advantage/disadvantage, since in many rules and situations an 18 might
    be better than a 19 or a 2 better than a 16.
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

    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)
    warnings.resetwarnings()
    logger.addHandler(logging.StreamHandler())

    return config


def main():
    """Load configuration and run the bot."""
    config = get_config()

    bot.run(
        token=config["MAIN"].get("authtoken"),
        reconnect=True,
        log_level=logging.WARNING,
    )


if __name__ == "__main__":
    main()
