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
"""Dice-rolling commands for MvKDiceBot (text, mention, and slash)."""

import collections
import functools

import discord
from discord import app_commands
from discord.ext import commands

import mvkroller

# Slash-command parameter descriptions, shared by the hybrid commands and their
# /r and /p slash aliases so the help text stays identical.
MVK_DICE_HELP = (
    "Dice to roll, e.g. '1d20 2d10 d8 2d6'. Add 'advantage'/'disadvantage' for the d20."
)
PLAIN_DICE_HELP = "Dice to roll plus +N/-N modifiers, e.g. '1d20 2d10 d8 +5'"

# How many recent text rolls to remember (message -> our reply) for edit handling.
MAX_TRACKED = 200


def echo_prefix(dicestr):
    """Quoted-subtext echo of the roll string, shown only for slash commands.

    A slash invocation isn't otherwise visible to the channel, so we echo it. The
    backticks keep any markdown or mentions in the string from being interpreted.
    """
    return f"> -# `{dicestr}`\n"


class Roll(commands.Cog):
    """MvK dice-rolling commands."""

    def __init__(self, bot):
        self.bot = bot
        # Text rolls remember `your message id -> (our reply, dice rolled)` so an
        # edit can update the same reply and re-roll only the dice that changed.
        self.replies = collections.OrderedDict()

    def _plainroller(self, channel_id):
        """A plainroll callable bound to the channel's current escalation die."""
        cog = self.bot.get_cog("Escalation")
        escalation = cog.current_escalation(channel_id) if cog else 0
        return functools.partial(mvkroller.plainroll, escalation=escalation)

    def _remember(self, message_id, reply, rolls):
        """Track (reply, rolls) for a trigger message, bounding the cache size."""
        self.replies[message_id] = (reply, rolls)
        self.replies.move_to_end(message_id)
        while len(self.replies) > MAX_TRACKED:
            self.replies.popitem(last=False)

    async def _respond_text(self, ctx, content, rolls):
        """Reply to a text roll, or edit our existing reply if it was edited."""
        existing = self.replies.get(ctx.message.id)
        if existing is not None:
            reply = existing[0]
            try:
                await reply.edit(content=content)
                self._remember(ctx.message.id, reply, rolls)
                return
            except discord.HTTPException:
                pass  # our reply is gone; fall through and post a fresh one
        reply = await ctx.reply(content)
        self._remember(ctx.message.id, reply, rolls)

    async def _run_text_roll(self, ctx, roller, dicestr):
        """Run a roller for a text/mention invocation (reply tracked, prior reused)."""
        existing = self.replies.get(ctx.message.id)
        prior = existing[1] if existing else None
        try:
            text, rolls = roller(dicestr, prior_rolls=prior)
        except mvkroller.RollError as exc:
            await self._respond_text(ctx, exc.getMessage(), None)
            raise
        await self._respond_text(ctx, text, rolls)

    async def _run_slash_roll(self, interaction, roller, dicestr):
        """Run a roller for a slash invocation (echo the input, no edit tracking)."""
        prefix = echo_prefix(dicestr)
        try:
            text, _ = roller(dicestr, prior_rolls=None)
        except mvkroller.RollError as exc:
            await interaction.response.send_message(prefix + exc.getMessage())
            raise
        await interaction.response.send_message(prefix + text)

    @commands.hybrid_command(aliases=["r", "R", "roll", "rolldice", "diceroll"])
    @app_commands.describe(dicestr=MVK_DICE_HELP)
    async def mvkroll(self, ctx, *, dicestr: str):
        """Rolls NdN format pool of dice and does MvK rules math for you.

        Usable as the '?roll'/'@MvkDiceBot roll' text command or the '/mvkroll'
        (alias '/r') slash command.

        Example: '?roll 1d20 2d10 d8 2d6'

        Add 'advantage' to discard lowest d20.
        Add 'disadvantage' to discard highest d20.
        Example: '?roll 2d20 2d10 advantage'
        Example: '?roll 2d20 2d10 disadvantage'

        Ignores anything extra it doesn't understand. Editing a text roll re-rolls
        only the dice you added and updates the same reply.
        """
        if ctx.interaction is None:
            await self._run_text_roll(ctx, mvkroller.mvkroll, dicestr)
        else:
            await self._run_slash_roll(ctx.interaction, mvkroller.mvkroll, dicestr)

    @commands.hybrid_command(
        aliases=[
            "p",
            "d",
            "D",
            "P",
            "pr",
            "PR",
            "justroll",
            "justdice",
            "plain",
            "dice",
        ]
    )
    @app_commands.describe(dicestr=PLAIN_DICE_HELP)
    async def plainroll(self, ctx, *, dicestr: str):
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
        roller = self._plainroller(ctx.channel.id)
        if ctx.interaction is None:
            await self._run_text_roll(ctx, roller, dicestr)
        else:
            await self._run_slash_roll(ctx.interaction, roller, dicestr)

    # Discord application commands have no alias mechanism, so the short '/r' and
    # '/p' forms are registered as their own slash commands that reuse the rollers.
    @app_commands.command(
        name="r", description="Roll a dice pool with MvK rules math (same as /mvkroll)"
    )
    @app_commands.describe(dicestr=MVK_DICE_HELP)
    async def mvkroll_slash_alias(self, interaction: discord.Interaction, dicestr: str):
        """Slash-command alias (/r) for /mvkroll."""
        await self._run_slash_roll(interaction, mvkroller.mvkroll, dicestr)

    @app_commands.command(
        name="p", description="Roll a dice pool and total it (same as /plainroll)"
    )
    @app_commands.describe(dicestr=PLAIN_DICE_HELP)
    async def plainroll_slash_alias(
        self, interaction: discord.Interaction, dicestr: str
    ):
        """Slash-command alias (/p) for /plainroll."""
        roller = self._plainroller(interaction.channel_id)
        await self._run_slash_roll(interaction, roller, dicestr)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Re-run an edited roll, reusing prior dice and editing our reply.

        Only this cog's roll commands are re-run, so stateful commands (like the
        escalation tracker) are never double-executed by a message edit.
        """
        if before.content == after.content:
            return
        ctx = await self.bot.get_context(after)
        if ctx.command is not None and ctx.cog is self:
            await self.bot.invoke(ctx)


async def setup(bot):
    """discord.py extension entry point: register the Roll cog."""
    await bot.add_cog(Roll(bot))
