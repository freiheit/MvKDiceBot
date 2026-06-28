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

import itertools

import discord
from discord import app_commands
from discord.ext import commands

import prefixstore

# Order of ?help sections (by cog name); the uncategorized help command is last.
SECTION_ORDER = ("Dice Rolling", "Escalation", "Configuration")
# Extra text appended to a section's heading in ?help.
HEADING_SUFFIX = {
    "Escalation": " (13th Age)",
    "Configuration": " (Server Managers only)",
}
# Heading for the help command's own (cog-less) section.
HELP_SECTION = "Help"


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
    """Help command that outputs Markdown (headings + bullets), not a code block.

    The built-in help command writes a fixed-width code block to ``ctx.channel``
    directly. Instead we render Markdown through ``ctx.send`` (see
    ``_HelpDestination``), which looks better in Discord and lets the same help
    command answer both ``?help`` and ``/help`` (the latter ephemerally). The
    ``paginator`` is created without code-fence prefix/suffix in ``setup`` so the
    Markdown isn't wrapped in ```` ``` ````.
    """

    def get_destination(self):
        return _HelpDestination(self.context)

    def _add_bullet(self, command):
        """Add a ``- **name** \u2014 short help`` bullet for a command."""
        bullet = f"- **{command.name}**"
        if command.short_doc:
            bullet += f" \u2014 {command.short_doc}"
        self.paginator.add_line(bullet)

    def _prefix_footer(self):
        """A footer line naming this server's prefixes plus @-mention and slash."""
        bot = self.context.bot
        store = getattr(bot, "prefix_store", None)
        guild_id = self.context.guild.id if self.context.guild else None
        prefixes = store.get(guild_id) if store else list(prefixstore.DEFAULT_PREFIXES)
        chars = prefixstore.format_prefixes(prefixes)
        lead = f"{chars} " if chars else ""
        return f"Command prefixes: {lead}@-me or slash-commands."

    async def send_bot_help(self, mapping, /):  # pylint: disable=unused-argument
        """Render the full command list as Markdown sections."""
        bot = self.context.bot
        name = bot.user.display_name if bot.user else "MvK Dice Bot"
        description = (bot.description or "").strip()
        title = f"## **{name}**"
        if description:
            title += f" \u2014 {description}"
        self.paginator.add_line(title)

        filtered = await self.filter_commands(bot.commands, sort=False)

        def category(command):
            return command.cog.qualified_name if command.cog is not None else None

        def order(command):
            key = category(command)
            if key is None:
                return (len(SECTION_ORDER) + 1, "")  # help command's section last
            if key in SECTION_ORDER:
                return (SECTION_ORDER.index(key), "")
            return (len(SECTION_ORDER), key)  # any other cog, alphabetical, before Help

        filtered.sort(key=order)

        for key, cmds in itertools.groupby(filtered, key=category):
            cmds = sorted(cmds, key=lambda c: c.name)
            if key is None:
                self.paginator.add_line(f"### {HELP_SECTION}")
                for command in cmds:
                    self._add_bullet(command)
                # Usage bullets describe the help command specifically, so use its
                # configured name rather than whichever cog-less command sorts first.
                help_name = self.context.bot.help_command.command_attrs.get(
                    "name", "help"
                )
                self.paginator.add_line(
                    f"- **{help_name} <command>** \u2014 for more info on a command"
                )
                self.paginator.add_line(
                    f"- **{help_name} <category>** \u2014 for more info on a category."
                )
            else:
                self.paginator.add_line(f"### {key}{HEADING_SUFFIX.get(key, '')}")
                for command in cmds:
                    self._add_bullet(command)

        self.paginator.add_line()
        self.paginator.add_line(self._prefix_footer())

        await self.send_pages()

    async def send_cog_help(self, cog, /):
        """Render a single category's commands as Markdown."""
        heading = cog.qualified_name + HEADING_SUFFIX.get(cog.qualified_name, "")
        self.paginator.add_line(f"## {heading}")
        if cog.description:
            self.paginator.add_line()
            self.paginator.add_line(cog.description)

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if filtered:
            self.paginator.add_line()
            for command in filtered:
                self._add_bullet(command)

        await self.send_pages()

    async def send_command_help(self, command, /):
        """Render one command's full help as Markdown (no code block)."""
        # Signature without a prefix (the user knows their prefix) and without the
        # alias list (get_command_signature folds those in as [name|alias...]);
        # aliases get their own line below instead.
        usage = command.qualified_name
        if command.signature:
            usage += f" {command.signature}"
        self.paginator.add_line(f"**{usage}**")

        help_text = command.help or command.short_doc
        if help_text:
            self.paginator.add_line()
            for line in help_text.split("\n"):
                self.paginator.add_line(line)

        if command.aliases:
            self.paginator.add_line()
            self.paginator.add_line(
                "Aliases: " + ", ".join(f"`{alias}`" for alias in command.aliases)
            )

        await self.send_pages()


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
    # No code-fence prefix/suffix so the help renders as Markdown, not a block.
    bot.help_command = HybridHelpCommand(
        paginator=commands.Paginator(prefix=None, suffix=None)
    )
    await bot.add_cog(Help(bot))
