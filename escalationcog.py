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
"""Escalation die tracker for MvKDiceBot (13th Age).

The escalation die runs 0-6: it starts at 0 (round 1, no bonus), advances by 1
each round to a maximum of 6, and resets to 0 between battles. Heroes add it to
their attack rolls. This cog tracks one value per channel, in memory, and lets a
channel's value lapse back to 0 after a period of inactivity.
"""

import time

from discord import app_commands
from discord.ext import commands

from rollcommon import NUMBER_EMOJI

MAX_VALUE = 6
# A channel's counter resets to 0 once it has gone untouched this long, so a
# forgotten battle doesn't leave a stale value lying around.
EXPIRY_SECONDS = 12 * 60 * 60


def next_value(current, action):
    """Return the new escalation-die value for ``action`` applied to ``current``.

    Recognized actions: '+'/'+1'/'up'/'next'/'advance' (increment, caps at
    MAX_VALUE), '-'/'-1'/'down'/'back' (decrement, floors at 0),
    'reset'/'new'/'end' (set to 0), or a bare number 0-MAX_VALUE (set directly).
    Raises ValueError for anything else.
    """
    action = action.strip().lower()

    if action in ("+", "+1", "up", "next", "advance"):
        return min(current + 1, MAX_VALUE)
    if action in ("-", "-1", "down", "back"):
        return max(current - 1, 0)
    if action in ("reset", "new", "end"):
        return 0
    if action.isdigit():
        value = int(action)
        if 0 <= value <= MAX_VALUE:
            return value

    raise ValueError(f"Unrecognized escalation action: {action!r}")


def format_value(value):
    """Render an escalation-die value as a header, big emoji, and subtext."""
    if value <= 0:
        detail = "No bonus yet"
    elif value >= MAX_VALUE:
        detail = f"Players get +{value} to attacks (maximum)"
    else:
        detail = f"Players get +{value} to attacks"
    return f"## Escalation Die Is\n# {NUMBER_EMOJI[value]}\n-# {detail}"


class EscalationTracker:
    """In-memory per-key escalation-die values that lapse to 0 after EXPIRY.

    ``now`` is injectable so the expiry behavior can be unit-tested.
    """

    def __init__(self, now=time.monotonic, expiry=EXPIRY_SECONDS):
        self._now = now
        self._expiry = expiry
        self._state = {}  # key -> (value, last_updated)

    def get(self, key):
        """Current value for ``key``, or 0 if unset or expired."""
        entry = self._state.get(key)
        if entry is None:
            return 0
        value, updated = entry
        if self._now() - updated > self._expiry:
            del self._state[key]
            return 0
        return value

    def set(self, key, value):
        """Store ``value`` for ``key`` and stamp it as just-updated."""
        self._state[key] = (value, self._now())
        return value


USAGE = (
    "Track the 13th Age escalation die (0-6). Usage: `?escalation` to show, "
    "`+1`/`next` to advance, `-1`/`back` to step down, `reset` for a new battle, "
    "or a number `0`-`6` to set it."
)


ACTION_HELP = "Blank to show; '+1'/'next', '-1'/'back', 'reset', or a number 0-6"


class Escalation(commands.Cog):
    """Tracks the 13th Age escalation die, one value per channel."""

    def __init__(self, bot):
        self.bot = bot
        self.tracker = EscalationTracker()

    def current_escalation(self, channel_id):
        """Current escalation die for a channel; used by other cogs (plainroll)."""
        return self.tracker.get(channel_id)

    async def _handle(self, channel_id, action, send):
        """Apply ``action`` to ``channel_id``'s value and reply via ``send``."""
        current = self.tracker.get(channel_id)

        if not action.strip():
            await send(format_value(current))
            return

        try:
            new_value = next_value(current, action)
        except ValueError:
            await send(USAGE)
            return

        self.tracker.set(channel_id, new_value)
        await send(format_value(new_value))

    @commands.hybrid_command(aliases=["esc", "e"])
    @app_commands.describe(action=ACTION_HELP)
    async def escalation(self, ctx, *, action: str = ""):
        """Show or change the escalation die for this channel.

        The escalation die (13th Age) starts at 0, goes up 1 per round to a max
        of 6, and resets between battles. Usable as '?escalation'/'/escalation'
        (text aliases '?esc', '?e'; also the '/esc' slash command). A channel's
        value resets to 0 after 12 hours of inactivity.
        """
        await self._handle(ctx.channel.id, action, ctx.reply)

    # Discord application commands have no alias mechanism, so '/esc' is its own
    # slash command reusing the same handler (there is intentionally no '/e').
    @app_commands.command(
        name="esc",
        description="Show or change the escalation die (same as /escalation)",
    )
    @app_commands.describe(action=ACTION_HELP)
    async def esc_slash_alias(self, interaction, action: str = ""):
        """Slash-command alias (/esc) for /escalation."""
        await self._handle(
            interaction.channel_id, action, interaction.response.send_message
        )

    @commands.hybrid_command(name="nextround", aliases=["next", "n"])
    async def nextround(self, ctx):
        """Advance the escalation die by a round (same as 'escalation next').

        Usable as '?nextround'/'/nextround' (text aliases '?next', '?n'; also the
        '/n' slash command).
        """
        await self._handle(ctx.channel.id, "next", ctx.reply)

    # As with '/esc', the '/n' slash form is its own command (no slash aliases).
    @app_commands.command(
        name="n", description="Advance the escalation die a round (same as /nextround)"
    )
    async def n_slash_alias(self, interaction):
        """Slash-command alias (/n) for /nextround."""
        await self._handle(
            interaction.channel_id, "next", interaction.response.send_message
        )


async def setup(bot):
    """discord.py extension entry point: register the Escalation cog."""
    await bot.add_cog(Escalation(bot))
