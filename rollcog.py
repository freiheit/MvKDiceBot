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
    "Dice + keywords: advantage/disadvantage, overwhelmed/staggered, "
    "boost/reduce dN, burnout, unstable, burst, +N, impact+N, vs N (see ?help)."
)
PLAIN_DICE_HELP = "Dice to roll plus +N/-N modifiers, e.g. '1d20 2d10 d8 +5'"
ANY_DICE_HELP = "Any dice (d2, d3, d7, d100, ...) plus +N/-N modifiers, e.g. 'd100 +17'"

# How many recent text rolls to remember (message -> our reply) for edit handling.
MAX_TRACKED = 200

# State kept per text-roll trigger message so edits can update the same reply,
# re-roll only the added dice, and show prior dice lines struck through.
#   reply   - the Message we sent
#   rolls   - the raw dice rolled (passed back in as prior_rolls on edit)
#   text    - the current roll's rendered body (its 'Dice:' line is struck next edit)
#   history - struck-through 'Dice:' lines from previous versions of this roll
RollState = collections.namedtuple("RollState", "reply rolls text history")


def echo_prefix(dicestr):
    """Quoted-subtext echo of the roll string, shown only for slash commands.

    A slash invocation isn't otherwise visible to the channel, so we echo it. The
    backticks keep any markdown or mentions in the string from being interpreted.
    """
    return f"> -# `{dicestr}`\n"


def dice_line(text):
    """Return the 'Dice: ...' line from a roll's rendered body, or None.

    The rollers render the dice as a quiet '-# Dice: ...' subtext line; the '-# '
    prefix is stripped so the history entry strikes through just the dice.
    """
    for line in text.split("\n"):
        stripped = line.removeprefix("-# ")
        if stripped.startswith("Dice:"):
            return stripped.rstrip()
    return None


def render_with_history(history, body):
    """Stack struck-through history lines (if any) above the current body."""
    if history:
        return "\n".join(history) + "\n" + body
    return body


class Roll(commands.Cog, name="Dice Rolling"):
    """Dice Rolling commands."""

    def __init__(self, bot):
        self.bot = bot
        # trigger message id -> RollState, for editing text rolls in place.
        self.replies = collections.OrderedDict()

    def _plainroller(self, channel_id):
        """A plainroll callable bound to the channel's current escalation die."""
        cog = self.bot.get_cog("Escalation")
        escalation = cog.current_escalation(channel_id) if cog else 0
        return functools.partial(mvkroller.plainroll, escalation=escalation)

    def _remember(self, message_id, state):
        """Track a RollState for a trigger message, bounding the cache size."""
        self.replies[message_id] = state
        self.replies.move_to_end(message_id)
        while len(self.replies) > MAX_TRACKED:
            self.replies.popitem(last=False)

    async def _post(self, ctx, content, state):
        """Reply to a text roll, or edit our existing reply, then store the state."""
        existing = self.replies.get(ctx.message.id)
        reply = existing.reply if existing else None
        if reply is not None:
            try:
                await reply.edit(content=content)
            except discord.HTTPException:
                reply = None  # our reply is gone; post a fresh one
        if reply is None:
            # Reply (so it threads under the trigger) but don't ping the author.
            reply = await ctx.reply(content, mention_author=False)
        self._remember(
            ctx.message.id, RollState(reply, state.rolls, state.text, state.history)
        )

    async def _run_text_roll(self, ctx, roller, dicestr):
        """Run a roller for a text/mention invocation (tracked, prior reused)."""
        prev = self.replies.get(ctx.message.id)
        prior_rolls = prev.rolls if prev else None
        prior_history = prev.history if prev else []
        prior_text = prev.text if prev else ""

        try:
            text, rolls = roller(dicestr, prior_rolls=prior_rolls)
        except mvkroller.RollError as exc:
            content = render_with_history(prior_history, exc.getMessage())
            await self._post(
                ctx, content, RollState(None, prior_rolls, prior_text, prior_history)
            )
            raise

        history = list(prior_history)
        previous = dice_line(prior_text)
        if previous:
            history.append(f"-# ~~{previous}~~")
        content = render_with_history(history, text)
        await self._post(ctx, content, RollState(None, rolls, text, history))

    async def _run_slash_roll(self, interaction, roller, dicestr):
        """Run a roller for a slash invocation (echo the input, no edit tracking)."""
        prefix = echo_prefix(dicestr)
        try:
            text, _ = roller(dicestr, prior_rolls=None)
        except mvkroller.RollError as exc:
            await interaction.response.send_message(prefix + exc.getMessage())
            raise
        await interaction.response.send_message(prefix + text)

    @commands.hybrid_command(
        aliases=["r", "R", "roll", "rolldice", "diceroll"],
        # brief is the ?help bullet (Markdown ok); description is the slash-UI text
        # (shown literally by Discord, so no Markdown there).
        brief="Rolls NdN format pool of dice and does **MvK** rules math for you.",
        description="Roll a dice pool with MvK rules math",
    )
    @app_commands.describe(dicestr=MVK_DICE_HELP)
    async def mvkroll(self, ctx, *, dicestr: str):
        """Rolls an NdN-format pool of dice and does MvK rules math for you.

        Example: `roll 1d20 2d10 d8 2d6`

        Add `advantage` to discard the lowest d20, or `disadvantage` to discard
        the highest. Example: `roll 2d20 2d10 advantage`

        Add `overwhelmed` or `staggered` (stress) to reduce your largest die one
        size before rolling; both together scratch it instead.
        Add `vs N` (or `counter N`) to compare your action total to a counter.
        Example: `roll 1d20 2d10 overwhelmed vs 21`

        More keywords:
        - `+N`/`-N` adjust the action total; `impact +N` adjusts impact.
        - `boost dN`/`reduce dN` step a die up/down a size before rolling
          (boosting a d12 adds a d4; reducing a d4 removes it).
        - `burnout` totals your highest three dice instead of two.
        - `unstable` applies `-1` to the action total; `burst` adds `+2` impact
          and rolls with disadvantage (add the doubled Drive die yourself).

        Ignores anything extra it doesn't understand. Editing a roll re-rolls only
        the dice you added and updates the same reply.
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
        ],
        brief=(
            "Rolls NdN format pool of dice. Only accepts d20, d12, d10, d8, d6 and "
            "d4 dice. With some **13th Age** extras."
        ),
        description="Roll dice and total them (with 13th Age extras)",
    )
    @app_commands.describe(dicestr=PLAIN_DICE_HELP)
    async def plainroll(self, ctx, *, dicestr: str):
        """Rolls a pool of dice for any d20 game, with some 13th Age extras.

        Only accepts d20, d12, d10, d8, d6 and d4 dice. Accepts multiple `+N` and
        `-N` modifiers and prints a total.

        For a single d20 it calls out likely special results (`20` = crit,
        `1` = fail, even/odd) and adds this channel's 13th Age escalation die to
        the roll (set it with the `escalation` command).

        Example: `justroll 1d20 2d10 d8 2d6 d6` (works out that it's 3d6)
        Example: `p 1d20 +5 +2` (adds 7 to whatever is rolled)

        Ignores anything it doesn't understand. Doesn't handle
        advantage/disadvantage, since an 18 might be better than a 19, or a 2
        better than a 16.
        """
        roller = self._plainroller(ctx.channel.id)
        if ctx.interaction is None:
            await self._run_text_roll(ctx, roller, dicestr)
        else:
            await self._run_slash_roll(ctx.interaction, roller, dicestr)

    @commands.hybrid_command(
        aliases=["a", "rollany"],
        brief="Rolls any dice (d2, d3, d7, d100, ...) and totals them.",
        description="Roll any dice and total them",
    )
    @app_commands.describe(dicestr=ANY_DICE_HELP)
    async def anyroll(self, ctx, *, dicestr: str):
        """Rolls a pool of dice of any size, plus `+N`/`-N` modifiers.

        Unlike `plainroll` it doesn't restrict die sizes, so `d100`, `3d3`, `d7`,
        `d2`, and so on all work. It just totals the dice and modifiers, with no
        special MvK or 13th Age rules and no crit/even/odd callouts.
        Example: `anyroll d100 +17`
        Example: `anyroll 3d3 d6`
        """
        if ctx.interaction is None:
            await self._run_text_roll(ctx, mvkroller.anyroll, dicestr)
        else:
            await self._run_slash_roll(ctx.interaction, mvkroller.anyroll, dicestr)

    # Discord application commands have no alias mechanism, so the short '/r',
    # '/p', and '/a' forms are registered as their own slash commands that reuse
    # the rollers.
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

    @app_commands.command(
        name="a", description="Roll any dice and total them (same as /anyroll)"
    )
    @app_commands.describe(dicestr=ANY_DICE_HELP)
    async def anyroll_slash_alias(self, interaction: discord.Interaction, dicestr: str):
        """Slash-command alias (/a) for /anyroll."""
        await self._run_slash_roll(interaction, mvkroller.anyroll, dicestr)

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
