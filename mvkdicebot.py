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
import random
import re
import warnings
from configparser import ConfigParser
import discord
from discord.ext import commands

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
    logger.warning(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.hybrid_command(aliases=["r", "R", "rolldice", "diceroll"])  # pylint: disable=no-member
async def roll(ctx, *, dicestr: str):
    """Rolls a pool of dice in NdN format.
    Example: '?roll 1d20 2d10 d8 2d6'

    Add 'advantage' to discard lowest d20.
    Add 'disadvantage' to discard highest d20.
    Example: '?roll 2d20 2d10 advantage'
    Example: '?roll 2d20 2d10 disadvantage'

    Ignores anything extra it doesn't understand.
    """
    # pylint: disable=logging-fstring-interpolation
    # pylint: disable=consider-using-dict-items
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-nested-blocks
    # pylint: disable=line-too-long

    logger.debug(f"roll: {dicestr}")

    cheat = False
    advantage = False
    disadvantage = False

    if re.search(r"disadvantage", dicestr, flags=re.IGNORECASE):
        disadvantage = True
    elif re.search(r"advantage", dicestr, flags=re.IGNORECASE):
        advantage = True

    if re.search(r"cheat", dicestr, flags=re.IGNORECASE):
        cheat = True

    # types of dice we're looking for:
    dicecounts = {
        20: 0,
        12: 0,
        10: 0,
        8: 0,
        6: 0,
        4: 0,
    }

    dicerolls = {
        20: [],
        12: [],
        10: [],
        8: [],
        6: [],
        4: [],
    }

    # dice d4-d12 are called "Character Dice" and the d20 is called the "Fortune Die"
    characterdicerolls = []  # non-d20 dice
    fortunedicerolls = []  # d20s

    pattern_ndn = re.compile(r"([0-9]*) *[dD]([0-9]+)")

    try:
        for count, size in re.findall(pattern_ndn, dicestr):
            logger.debug(f"roll: count={count} size={size}")
            size = int(size)
            if len(count) >= 1:
                count = int(count)
            elif len(count) < 1 or int(count) < 1:
                count = 1
            if size in dicecounts:
                dicecounts[size] += count
            else:
                await ctx.reply(f"Invalid dice size d{size}")
    except Exception:
        await ctx.reply("Error parsing dice rolls. No NdN?")
        raise

    try:
        for size in dicecounts:
            if dicecounts[size] > 0:
                # logger.debug(f"rolling: d{size}={dicecounts[size]}")
                dicerolls[size] = []
                # pylint: disable=unused-variable
                for i in range(0, dicecounts[size]):
                    if cheat:
                        result = size
                    else:
                        result = random.randint(1, size)
                    dicerolls[size].append(result)
                    if size == 20:
                        fortunedicerolls.append(result)
                    else:
                        characterdicerolls.append(result)
    except Exception:
        await ctx.reply("Coding error rolling dice.")
        raise

    fortunedicerolls.sort(reverse=True)
    characterdicerolls.sort(reverse=True)

    try:
        if (
            len(
                dicerolls[20]
                + dicerolls[12]
                + dicerolls[10]
                + dicerolls[8]
                + dicerolls[6]
                + dicerolls[4]
            )
            > 0
        ):
            answer = ""
            if cheat:
                answer += "# Cheating\n"

            try:
                if advantage or disadvantage:
                    logger.debug(f"Dicecounts: {dicecounts}")
                    logger.debug(f"Dicerolls: {dicerolls}")
                    if dicecounts[20] >= 2 and len(dicerolls[20]) >= 2:
                        answer += "Original d20s: "
                        answer += f"{len(dicerolls[20])}d20{ str(dicerolls[20])} -- "
                        if advantage:
                            answer += "Applying _advantage_...\n\n"
                            dicerolls[20].sort(reverse=True)
                            logger.debug(f"advantage rolls {dicerolls[20]}")
                        if disadvantage:
                            answer += "Applying _disadvantage_...\n\n"
                            dicerolls[20].sort()
                            logger.debug(f"disadvantage rolls {dicerolls[20]}")
                        retained_d20 = dicerolls[20][0]
                        dicerolls[20] = [retained_d20]
                    else:
                        answer += (
                            "## Advantage and Disadvantage require 2 or more d20s\n"
                        )
                        answer += "Rolling normally...\n\n"
                        advantage = False
                        disadvantage = False
            except Exception:
                await ctx.reply("Coding error calculating advantage or disadvantage.")
                raise

            try:
                answer += "Dice: "
                for size in dicerolls:
                    if len(dicerolls[size]) > 0:
                        answer += (
                            f"{len(dicerolls[size])}d{size}{ str(dicerolls[size])} "
                        )
                answer += "\n"
            except Exception:
                await ctx.reply("Coding error displaying Dice")
                raise

            try:
                flatdicerolls = (
                    dicerolls[20]
                    + dicerolls[12]
                    + dicerolls[10]
                    + dicerolls[8]
                    + dicerolls[6]
                    + dicerolls[4]
                )
                flatdicerolls.sort(reverse=True)
            except Exception:
                await ctx.reply(
                    "Coding error flattening dice rolls into single sorted list."
                )
                raise

            try:
                action_dice = flatdicerolls[:2]
                action_total = sum(action_dice)
                answer += f"**Action Total: {str(action_total)}** {str(action_dice)}\n"
            except Exception:
                await ctx.reply("Coding error calculating Action Total.")
                raise

            try:
                # die results of 10 or higher on a d10 or 12 give two impact. It doesn't happen on a d20.
                fortuneimpact = 1 if dicerolls[20][0] >= 4 else 0
                doublecharacterimpact = sum(2 for p in characterdicerolls if p >= 10)
                characterimpact = sum(1 for p in characterdicerolls if 4 <= p < 10)
                impact = fortuneimpact + doublecharacterimpact + characterimpact
                impact = max(impact, 1)
                answer += f"**Impact: {impact}** "
                answer += f"(fortune={fortuneimpact} 2x={doublecharacterimpact} 1x={characterimpact})"
            except Exception:
                await ctx.reply("Coding error calculating Impact")
                raise

            if cheat:
                answer += "\n# Cheating"

            await ctx.reply(answer)
        else:
            await ctx.reply(f"No valid NdNs found in '{dicestr}'")
    except Exception:
        await ctx.reply("Coding error calculating totals.")
        raise


#    try:
#        rolls, limit = map(int, dicestr.split("d"))
#    except Exception:
#        await ctx.send("Format has to be in NdN!")
#        return

#    result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
#    await ctx.send(result)


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
