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

# Guild IDs to register slash commands in directly, for instant updates instead
# of waiting on global propagation. Populated from the config's `primary_guilds`
# in main(); an empty list means "sync globally". Mutated in place (not
# reassigned) so setup_hook sees the configured value.
primary_guild_ids = []

intents = discord.Intents.default()
# intents.members = True
# intents.messages = True
intents.message_content = True  # pylint: disable=assigning-non-slot

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("?"),
    description=DESCRIPTION,
    intents=intents,
)


class _HelpDestination:  # pylint: disable=too-few-public-methods
    """Routes help output through a context, ephemerally.

    ``ephemeral=True`` makes ``/help`` visible only to the user who ran it (the
    "Only you can see this" style). It is silently ignored for the text
    ``?help`` command, which stays visible to the channel as before.
    """

    def __init__(self, ctx):
        self.ctx = ctx

    async def send(self, *args, **kwargs):
        """Send through the context as an ephemeral reply."""
        return await self.ctx.send(*args, ephemeral=True, **kwargs)


class HybridHelpCommand(commands.DefaultHelpCommand):
    """Default help command that sends output through the context.

    The built-in help command writes to ``ctx.channel`` directly, which would
    leave a slash-command interaction unacknowledged. Sending through
    ``ctx.send`` instead lets the same help command answer both the ``?help``
    text command and the ``/help`` slash command (see ``help_slash``), and makes
    the ``/help`` reply ephemeral.
    """

    def get_destination(self):
        return _HelpDestination(self.context)


bot.help_command = HybridHelpCommand()


@bot.tree.command(  # pylint: disable=no-member
    name="help", description="Show the list of commands and how to use them"
)
@app_commands.describe(command="Optional command name to show detailed help for")
async def help_slash(interaction: discord.Interaction, command: str | None = None):
    """Slash-command (/help) equivalent of the '?help' text command."""
    ctx = await commands.Context.from_interaction(interaction)
    if command:
        await ctx.send_help(command)
    else:
        await ctx.send_help()


@bot.event
async def setup_hook():
    """Register application (slash) commands with Discord on startup.

    The commands are declared as hybrid/tree commands, so discord.py already has
    the slash-command definitions in the command tree; syncing tells Discord
    about them.

    If one or more primary guilds are configured (``primary_guilds`` in the
    config -- "guild" is the Discord API term for a server), the commands are
    copied to each of those guilds and synced there, which is instant. Any
    leftover global commands are then cleared so a guild doesn't show each
    command twice. Otherwise a global sync is done, which can take up to ~1 hour
    to propagate the first time.
    """
    try:
        if primary_guild_ids:
            for guild_id in primary_guild_ids:
                guild = discord.Object(id=guild_id)
                bot.tree.copy_global_to(guild=guild)
                synced = await bot.tree.sync(guild=guild)
                logger.warning(
                    "Synced %d application command(s) to guild %d",
                    len(synced),
                    guild_id,
                )
            # Drop any previously-registered global commands so the primary
            # guilds don't end up showing each command twice.
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
        else:
            synced = await bot.tree.sync()
            logger.warning("Synced %d application command(s) globally", len(synced))
    except Exception:  # pylint: disable=broad-except
        logger.exception("Failed to sync application commands")


@bot.event
async def on_ready():
    """Log when we start up"""
    # pylint: disable=logging-fstring-interpolation
    logger.warning(f"Logged in as {bot.user} (ID {bot.user.id})")


async def _do_roll(send, roll_func, dicestr):
    """Run a roller and send its output (or the error message) via ``send``.

    ``send`` is a coroutine that takes a single string: ``ctx.reply`` for the
    text/hybrid commands or ``interaction.response.send_message`` for the slash
    aliases. Re-raises RollError after reporting it so it is still logged.
    """
    try:
        await send(roll_func(dicestr))
    except mvkroller.RollError as exc:
        await send(exc.getMessage())
        raise


@bot.hybrid_command(aliases=["r", "R", "roll", "rolldice", "diceroll"])  # pylint: disable=no-member
@app_commands.describe(
    dicestr="Dice to roll, e.g. '1d20 2d10 d8 2d6'. Add 'advantage'/'disadvantage' for the d20."
)
async def mvkroll(ctx, *, dicestr: str):
    """Rolls NdN format pool of dice and does MvK rules math for you.

    Usable as the '?roll'/'@MvkDiceBot roll' text command or the '/mvkroll'
    (alias '/r') slash command.

    Example: '?roll 1d20 2d10 d8 2d6'

    Add 'advantage' to discard lowest d20.
    Add 'disadvantage' to discard highest d20.
    Example: '?roll 2d20 2d10 advantage'
    Example: '?roll 2d20 2d10 disadvantage'

    Ignores anything extra it doesn't understand.
    """
    await _do_roll(ctx.reply, mvkroller.mvkroll, dicestr)


@bot.hybrid_command(
    aliases=["p", "d", "D", "P", "pr", "PR", "justroll", "justdice", "plain", "dice"]
)  # pylint: disable=no-member
@app_commands.describe(
    dicestr="Dice to roll plus +N/-N modifiers, e.g. '1d20 2d10 d8 +5'"
)
async def plainroll(ctx, *, dicestr: str):
    """Rolls NdN format pool of dice. Only accepts d20, d12, d10, d8, d6 and d4 dice.

    Usable as the '?p'/'@MvkDiceBot plainroll' text command or the '/plainroll'
    (alias '/p') slash command.

    For single d20, may call out likely special things like 20=crit, 1=fail, even and odd.

    Accepts multiple +N and -N modifiers.

    Prints a total of all the dice and the modifiers.

    Example: '?justroll 1d20 2d10 d8 2d6 d6' (note: will work out that it's 3d6)
    Example: '?p 1d20 +5 +2' (note: will add 7 to whatever is rolled)

    Ignores anything extra it doesn't understand.  Doesn't handle
    advantage/disadvantage, since in many rules and situations an 18 might
    be better than a 19 or a 2 better than a 16.
    """
    await _do_roll(ctx.reply, mvkroller.plainroll, dicestr)


# Discord application commands have no alias mechanism, so the short '/r' and
# '/p' forms are registered as their own slash commands that reuse the rollers.
@bot.tree.command(  # pylint: disable=no-member
    name="r", description="Roll a dice pool with MvK rules math (same as /mvkroll)"
)
@app_commands.describe(
    dicestr="Dice to roll, e.g. '1d20 2d10 d8 2d6'. Add 'advantage'/'disadvantage' for the d20."
)
async def mvkroll_slash_alias(interaction: discord.Interaction, dicestr: str):
    """Slash-command alias (/r) for /mvkroll."""
    await _do_roll(interaction.response.send_message, mvkroller.mvkroll, dicestr)


@bot.tree.command(  # pylint: disable=no-member
    name="p", description="Roll a dice pool and total it (same as /plainroll)"
)
@app_commands.describe(
    dicestr="Dice to roll plus +N/-N modifiers, e.g. '1d20 2d10 d8 +5'"
)
async def plainroll_slash_alias(interaction: discord.Interaction, dicestr: str):
    """Slash-command alias (/p) for /plainroll."""
    await _do_roll(interaction.response.send_message, mvkroller.plainroll, dicestr)


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

    # `primary_guilds` is an optional comma/whitespace-separated list of guild
    # (server) IDs to register slash commands in directly. Mutate the list in
    # place so setup_hook sees it without needing a global statement.
    raw_guilds = config["MAIN"].get("primary_guilds", "")
    primary_guild_ids.extend(
        int(guild_id) for guild_id in raw_guilds.replace(",", " ").split()
    )

    bot.run(
        token=config["MAIN"].get("authtoken"),
        reconnect=True,
        log_level=logging.WARNING,
    )


if __name__ == "__main__":
    main()
