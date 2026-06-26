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

import discord
from discord.ext import commands

import mvkconfig

__version__ = "1.0.0"
DESCRIPTION = """A dice rolling bot for MvK
"""

# Module-level logger; level/handlers are configured by mvkconfig.get_config().
logger = logging.getLogger(__name__)

# Cogs (loaded as discord.py extensions in setup_hook). Each module provides the
# commands and an `async def setup(bot)` entry point.
EXTENSIONS = ("rollcog", "helpcog", "escalationcog")

# Guild IDs to register slash commands in directly, for instant updates instead
# of waiting on global propagation. Populated from the config in main(); an empty
# list means "sync globally". Mutated in place (not reassigned) so setup_hook
# sees the configured value.
primary_guild_ids = []

intents = discord.Intents.default()
# intents.members = True
# intents.messages = True
intents.message_content = True  # pylint: disable=assigning-non-slot

bot = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or("?", "/"),
    description=DESCRIPTION,
    intents=intents,
)


@bot.event
async def setup_hook():
    """Load the command cogs and register slash commands with Discord on startup.

    The cogs put their slash-command definitions in the command tree; syncing
    tells Discord about them. If one or more primary guilds are configured
    (``primary_guilds`` in the config -- "guild" is the Discord API term for a
    server), the commands are copied to each of those guilds and synced there,
    which is instant; any leftover global commands are then cleared so a guild
    doesn't show each command twice. Otherwise a global sync is done, which can
    take up to ~1 hour to propagate the first time.
    """
    for extension in EXTENSIONS:
        await bot.load_extension(extension)

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


@bot.tree.error
async def on_app_command_error(interaction, error):
    """Log slash-command errors and make sure the interaction gets a reply.

    A slash command acknowledges Discord by responding to the interaction.
    Without this, an unexpected error (or a too-long response) before that
    happens leaves the interaction unanswered, which Discord shows the user as
    "This interaction failed". If the command already replied (e.g. a RollError
    message), is_done() is true and we only log.
    """
    logger.error("Error in application command %s", interaction.command, exc_info=error)
    if not interaction.response.is_done():
        try:
            await interaction.response.send_message(
                "Sorry, something went wrong running that command.", ephemeral=True
            )
        except discord.HTTPException:
            logger.exception("Failed to send application command error message")


def main():
    """Load configuration and run the bot."""
    config = mvkconfig.get_config()
    primary_guild_ids.extend(mvkconfig.get_primary_guild_ids(config))

    bot.run(
        token=config["MAIN"].get("authtoken"),
        reconnect=True,
        log_level=logging.WARNING,
    )


if __name__ == "__main__":
    main()
