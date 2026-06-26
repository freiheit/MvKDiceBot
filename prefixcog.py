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
"""Per-guild command-prefix configuration for MvKDiceBot.

Provides the ``setprefixes`` command (restricted to the guild owner,
administrators, or members with Manage Server) for showing or changing a server's
text command prefixes. It's a hybrid command, so it works as a text/prefix
command, via @-mention, and as the ``/setprefixes`` slash command. The values
live in ``bot.prefix_store`` (see prefixstore.py), which the bot's prefix resolver
reads for every message.
"""

import logging

from discord import app_commands
from discord.ext import commands

import prefixstore

logger = logging.getLogger(__name__)

SETPREFIXES_HELP = (
    "Characters to use as prefixes, e.g. '?/!' (replaces the current set); "
    "'none' for only @-mention and slash commands; blank to show the current set."
)

# Arguments that mean "no text prefixes" (only @-mention and slash commands).
CLEAR_WORDS = ("none", "clear", "off")


def may_manage_prefixes(ctx):
    """True if ``ctx.author`` may change prefixes: owner, admin, or Manage Server.

    Explicit (rather than only ``manage_guild``) so the guild owner always
    qualifies even with no role granting Manage Server, which also makes ``?help``
    list the command for them. Raises so command checks report the right reason.
    """
    if ctx.guild is None:
        raise commands.NoPrivateMessage()
    perms = ctx.author.guild_permissions
    if ctx.author.id == ctx.guild.owner_id or perms.administrator or perms.manage_guild:
        return True
    raise commands.MissingPermissions(["manage_guild"])


def can_manage_prefixes():
    """The command check wrapping :func:`may_manage_prefixes`."""
    return commands.check(may_manage_prefixes)


def describe(prefixes):
    """Phrase a guild's prefix list for a reply."""
    if not prefixes:
        return "none (only @-mention and slash commands)"
    return (
        f"{prefixstore.format_prefixes(prefixes)} (plus @-mention and slash commands)"
    )


class Prefixes(commands.Cog, name="Configuration"):
    """Per-guild command-prefix configuration.

    The cog's display name ("Configuration") is the heading it gets in ``?help``.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setprefixes",
        description="Show or set this server's text command prefixes",
    )
    @commands.guild_only()
    @can_manage_prefixes()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(prefixes=SETPREFIXES_HELP)
    async def setprefixes(self, ctx, *, prefixes: str = ""):
        """Show or set this server's text command prefixes.

        With no argument, shows the current prefixes. Otherwise sets them to the
        given characters (e.g. `?/!`), or `none` to use only @-mention and slash
        commands. The bot always also responds to @-mentions and its slash
        commands regardless. Requires being the server owner, an administrator, or
        having Manage Server.
        """
        # Acknowledge a slash interaction up front so the response can't miss the
        # 3-second deadline; a no-op (typing) for text/mention invocations.
        if ctx.interaction is not None:
            await ctx.defer(ephemeral=True)

        store = self.bot.prefix_store
        guild_id = ctx.guild.id
        arg = prefixes.strip()

        if not arg:
            await ctx.send(
                f"Current prefixes: {describe(store.get(guild_id))}", ephemeral=True
            )
            return

        if arg.lower() in CLEAR_WORDS:
            store.set(guild_id, [])
            logger.info("Guild %s cleared text prefixes", guild_id)
            await ctx.send(f"Prefixes set to {describe([])}", ephemeral=True)
            return

        parsed = prefixstore.parse_prefixes(arg)
        if not parsed:
            await ctx.send(
                "Give me one or more characters to use as prefixes (e.g. `?/!`), "
                "or `none` for only @-mention and slash commands.",
                ephemeral=True,
            )
            return

        store.set(guild_id, parsed)
        logger.info("Guild %s set prefixes to %s", guild_id, parsed)
        await ctx.send(f"Prefixes set to {describe(parsed)}", ephemeral=True)

    @setprefixes.error
    async def setprefixes_error(self, ctx, error):
        """Reply plainly when the check fails (wrong permission or used in a DM)."""
        original = getattr(error, "original", error)
        if isinstance(original, commands.NoPrivateMessage):
            await ctx.send("That command only works in a server.", ephemeral=True)
        elif isinstance(original, commands.CheckFailure):
            await ctx.send(
                "You need to be the server owner or have Administrator or "
                "**Manage Server** to change prefixes.",
                ephemeral=True,
            )
        else:
            logger.error("setprefixes failed", exc_info=original)


async def setup(bot):
    """discord.py extension entry point: ensure a prefix store and register the cog.

    ``main()`` normally attaches the real (file-backed) store to the bot before
    startup; fall back to an in-memory store so the cog can be loaded on its own
    (e.g. in tests).
    """
    if getattr(bot, "prefix_store", None) is None:
        bot.prefix_store = prefixstore.PrefixStore(":memory:").load()
    await bot.add_cog(Prefixes(bot))
