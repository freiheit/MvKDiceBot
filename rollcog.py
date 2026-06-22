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


async def _do_roll(send, roll_func, dicestr, echo_input=False):
    """Run a roller and send its output (or the error message) via ``send``.

    ``send`` is a coroutine that takes a single string: ``ctx.reply`` for the
    text/hybrid commands or ``interaction.response.send_message`` for the slash
    aliases. Re-raises RollError after reporting it so it is still logged.

    When ``echo_input`` is set, the original roll string is prepended as a
    quoted subtext line with the input in inline code (``> -# `...` ``). Slash
    commands enable this because, unlike a text reply, the invocation isn't
    otherwise visible to the channel; the backticks also stop any markdown or
    mentions in the echoed string from being interpreted.
    """
    prefix = f"> -# `{dicestr}`\n" if echo_input else ""
    try:
        await send(prefix + roll_func(dicestr))
    except mvkroller.RollError as exc:
        await send(prefix + exc.getMessage())
        raise


class Roll(commands.Cog):
    """MvK dice-rolling commands."""

    def __init__(self, bot):
        self.bot = bot

    def _plainroller(self, channel_id):
        """A plainroll callable bound to the channel's current escalation die."""
        cog = self.bot.get_cog("Escalation")
        escalation = cog.current_escalation(channel_id) if cog else 0
        return functools.partial(mvkroller.plainroll, escalation=escalation)

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

        Ignores anything extra it doesn't understand.
        """
        await _do_roll(
            ctx.reply,
            mvkroller.mvkroll,
            dicestr,
            echo_input=ctx.interaction is not None,
        )

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
        await _do_roll(
            ctx.reply,
            self._plainroller(ctx.channel.id),
            dicestr,
            echo_input=ctx.interaction is not None,
        )

    # Discord application commands have no alias mechanism, so the short '/r' and
    # '/p' forms are registered as their own slash commands that reuse the rollers.
    @app_commands.command(
        name="r", description="Roll a dice pool with MvK rules math (same as /mvkroll)"
    )
    @app_commands.describe(dicestr=MVK_DICE_HELP)
    async def mvkroll_slash_alias(self, interaction: discord.Interaction, dicestr: str):
        """Slash-command alias (/r) for /mvkroll."""
        await _do_roll(
            interaction.response.send_message,
            mvkroller.mvkroll,
            dicestr,
            echo_input=True,
        )

    @app_commands.command(
        name="p", description="Roll a dice pool and total it (same as /plainroll)"
    )
    @app_commands.describe(dicestr=PLAIN_DICE_HELP)
    async def plainroll_slash_alias(
        self, interaction: discord.Interaction, dicestr: str
    ):
        """Slash-command alias (/p) for /plainroll."""
        await _do_roll(
            interaction.response.send_message,
            self._plainroller(interaction.channel_id),
            dicestr,
            echo_input=True,
        )


async def setup(bot):
    """discord.py extension entry point: register the Roll cog."""
    await bot.add_cog(Roll(bot))
