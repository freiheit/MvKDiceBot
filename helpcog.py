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
"""Help command for MvKDiceBot, usable as both ?help and /help."""

import discord
from discord import app_commands
from discord.ext import commands


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
    text command and the ``/help`` slash command (see ``Help.help_slash``), and
    makes the ``/help`` reply ephemeral.
    """

    def get_destination(self):
        return _HelpDestination(self.context)


class Help(commands.Cog):
    """Provides the /help slash command (text ?help is bot.help_command)."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="Show the list of commands and how to use them"
    )
    @app_commands.describe(command="Optional command name to show detailed help for")
    async def help_slash(
        self, interaction: discord.Interaction, command: str | None = None
    ):
        """Slash-command (/help) equivalent of the '?help' text command."""
        ctx = await commands.Context.from_interaction(interaction)
        if command:
            await ctx.send_help(command)
        else:
            await ctx.send_help()


async def setup(bot):
    """discord.py extension entry point: install the help command and cog."""
    bot.help_command = HybridHelpCommand()
    await bot.add_cog(Help(bot))
