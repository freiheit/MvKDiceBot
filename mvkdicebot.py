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

import asyncio
import discord
import logging
import os
import random
import re
import warnings

from configparser import ConfigParser
from discord.ext import commands

__version__ = "0.0.1"
description = """A dice rolling bot for MvK
"""

intents = discord.Intents.default()
# intents.members = True
# intents.messages = True
intents.message_content = True

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("?"),
    description=description,
    intents=intents,
)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.hybrid_command()
async def roll(ctx, *, dicestr: str):
    """Rolls a pool of dice in NdN format.
    Example: '?roll 1d20 2d10 d8 2d6'
    Ignores anything extra it doesn't understand.
    """
    logger.debug(f"roll: {dicestr}")

    # types of dice we're looking for:
    dicecounts = { 20:0, 12:0,
      10: 0,
      8: 0,
      6: 0,
      4: 0,
    }
    
    dicerolls = {}
    flatdicerolls = []

    patternNdN = re.compile(r'([0-9]*)d([0-9]+)')
    
    for (count, size) in re.findall(patternNdN, dicestr):
        logger.debug(f"roll: count={count} size={size}")
        size=int(size)
        if len(count) >= 1:
            count=int(count)
        elif len(count) < 1 or int(count) < 1:
            count=1
        if size in dicecounts:
            dicecounts[size] += count
        else:
            await ctx.send(f"Invalid dice size d{size}")

    flatdicerolls = []

    for size in dicecounts:
        if dicecounts[size] > 0:
            # logger.debug(f"rolling: d{size}={dicecounts[size]}")   
            dicerolls[size] = []
            for i in range(0, dicecounts[size]):
                result = (random.randint(1,size))
                dicerolls[size].append(result)
                flatdicerolls.append(result)

    flatdicerolls.sort(reverse=True)

    if len(dicerolls) > 0:
        answer = "Dice: "
        for size in dicerolls:
           answer += f"**{len(dicerolls[size])}d{size}**{ str(dicerolls[size])} "
        answer += "\n"
        action_dice = flatdicerolls[:2]
        action_total = sum(action_dice)
        answer += f"Action Total: {str(action_total)} {str(action_dice)}\n"
        await ctx.send(answer)
    else:
        await ctx.send(f"No valid NdNs found in '{dicestr}'")
                
#    try:
#        rolls, limit = map(int, dicestr.split("d"))
#    except Exception:
#        await ctx.send("Format has to be in NdN!")
#        return

#    result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
#    await ctx.send(result)


class ImproperlyConfigured(Exception):
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
