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
import prefixstore

__version__ = "1.0.0"
DESCRIPTION = """A dice rolling bot for Mecha Vs Kaiju (MvK) and 13th Age
"""

# Module-level logger; level/handlers are configured by mvkconfig.get_config().
logger = logging.getLogger(__name__)

# Cogs (loaded as discord.py extensions in setup_hook). Each module provides the
# commands and an `async def setup(bot)` entry point.
EXTENSIONS = ("rollcog", "helpcog", "escalationcog", "prefixcog")

# Guild IDs to register slash commands in directly, for instant updates instead
# of waiting on global propagation. Populated from the config in main(); an empty
# list means "sync globally". Mutated in place (not reassigned) so setup_hook
# sees the configured value.
primary_guild_ids = []

intents = discord.Intents.default()
# intents.members = True
# intents.messages = True
intents.message_content = True  # pylint: disable=assigning-non-slot


async def get_prefix(the_bot, message):
    """Resolve the command prefixes for a message.

    Always includes the two @-mention forms, plus the guild's configured text
    prefixes from ``the_bot.prefix_store`` (the defaults when a guild hasn't set
    any, or in DMs). Slash commands are separate application commands and work
    regardless of this.
    """
    store = getattr(the_bot, "prefix_store", None)
    guild_id = message.guild.id if message.guild else None
    prefixes = store.get(guild_id) if store else list(prefixstore.DEFAULT_PREFIXES)
    return commands.when_mentioned_or(*prefixes)(the_bot, message)


bot = commands.AutoShardedBot(
    command_prefix=get_prefix,
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
    """Log when we start up, and seed default prefixes on first run.

    The first time the bot runs with a brand-new database, seed the classic
    ``?``/``/`` prefixes onto the guilds it's already in so they keep working;
    guilds joined afterwards start mention/slash only. Guarded so it runs once
    even though on_ready can fire again on reconnects.
    """
    # pylint: disable=logging-fstring-interpolation
    logger.warning(f"Logged in as {bot.user} (ID {bot.user.id})")

    store = getattr(bot, "prefix_store", None)
    if store is not None and store.created:
        seeded = store.backfill(guild.id for guild in bot.guilds)
        store.created = False
        logger.warning("Seeded default prefixes for %d existing guild(s)", seeded)


@bot.tree.error
async def on_app_command_error(interaction, error):
    """Log slash-command errors and make sure the interaction gets a reply.

    A slash command acknowledges Discord by responding to the interaction.
    Without this, an unexpected error (or a too-long response) before that
    happens leaves the interaction unanswered, which Discord shows the user as
    "This interaction failed". If the command already replied (e.g. a RollError
    message), is_done() is true and we only log.
    """
    # A failed permission/guild check isn't a bug -- tell the user plainly.
    if isinstance(error, discord.app_commands.CheckFailure):
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "You don't have permission to use that command.", ephemeral=True
                )
            except discord.HTTPException:
                logger.exception("Failed to send permission error message")
        return

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

    # Load per-guild prefixes once at startup; changes are written through to the
    # database as they happen (see prefixstore / prefixcog).
    bot.prefix_store = prefixstore.PrefixStore(
        mvkconfig.get_database_path(config)
    ).load()

    bot.run(
        token=config["MAIN"].get("authtoken"),
        reconnect=True,
        log_level=logging.WARNING,
    )


if __name__ == "__main__":
    main()
