#!.venv/bin/python3
# MvKRoller: Dice roller for the MvK Dice Bot
# Copyright (C) 2023 Eric Eisenhart
# edited by CJ Holmes
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# https://github.com/freiheit/MvKDiceBot
"""Common dice helpers shared by both rollers (parsing, rolling, display)."""

import logging
import random
import re

logger = logging.getLogger(__name__)

# Keycap emoji for small integers, used in Discord output by both the rollers
# (escalation line in plainroll) and the escalation tracker cog.
NUMBER_EMOJI = {
    0: ":zero:",
    1: ":one:",
    2: ":two:",
    3: ":three:",
    4: ":four:",
    5: ":five:",
    6: ":six:",
    7: ":seven:",
    8: ":eight:",
    9: ":nine:",
}


class RollError(Exception):
    """Boring Exception Class"""

    message = ""

    def __init__(self, msg):
        self.message = msg

    # pylint: disable=invalid-name
    def getMessage(self):
        """return this exception's message"""
        return self.message


def parse_dice(dicestr: str):
    """Parses the dice string and returns a dictionary of dieSize->count"""
    # types of dice we're looking for:
    dicecounts = {
        20: 0,
        12: 0,
        10: 0,
        8: 0,
        6: 0,
        4: 0,
    }

    pattern_ndn = re.compile(r"([0-9]*) *[dD]([0-9]+)")

    try:
        for count, size in re.findall(pattern_ndn, dicestr):
            logger.debug("Roll count=%s size=%s", count, size)
            size = int(size)
            if len(count) >= 1:
                count = int(count)
            elif len(count) < 1 or int(count) < 1:
                count = 1
            if size in dicecounts:
                dicecounts[size] += count
            else:
                raise RollError(f"Invalid dice size d{size}")
    except Exception as exc:
        raise RollError("Exception while parsing dice.") from exc

    return dicecounts


def _roll_one(size, rand_source):
    """Roll a single die of the given size with the given random.Random."""
    return int(rand_source.random() * size) + 1


def _empty_dicerolls():
    return {20: [], 12: [], 10: [], 8: [], 6: [], 4: []}


def roll_dice(dicecounts, rand_source=None):
    """Returns a dictionary of dieSize => rolls[]

    A `rand_source` (a random.Random instance) may be supplied so tests can roll
    deterministically; by default a fresh random.Random() is used.
    """
    dicerolls = _empty_dicerolls()

    try:
        if rand_source is None:
            rand_source = random.Random()

        for size, num in dicecounts.items():
            if num > 0:
                dicerolls[size] = [
                    _roll_one(size, rand_source) for idx in range(0, num)
                ]
    except Exception as exc:
        raise RollError("Exception while rolling dice.") from exc

    return dicerolls


def merge_rolls(prior, dicecounts, rand_source=None):
    """Reuse prior per-size rolls, rolling only the newly-added dice.

    For each die size, keep up to ``dicecounts[size]`` of ``prior``'s rolls and
    roll any additional dice; if the count dropped, a random subset of the prior
    rolls is kept (so editing down doesn't always discard the same dice). This
    makes editing a roll re-roll only the dice that were added, leaving the others
    as they were.
    """
    dicerolls = _empty_dicerolls()

    try:
        if rand_source is None:
            rand_source = random.Random()

        for size in dicerolls:
            want = dicecounts.get(size, 0)
            have = list(prior.get(size, []))
            kept = rand_source.sample(have, want) if want < len(have) else have
            extra = [_roll_one(size, rand_source) for _ in range(want - len(kept))]
            dicerolls[size] = kept + extra
    except Exception as exc:
        raise RollError("Exception while merging dice rolls.") from exc

    return dicerolls


def print_dice(dicerolls):
    "Creates a string rep of the rolled dice"
    answer = "Dice: "
    try:
        for size, values in dicerolls.items():
            if len(values) > 0:
                answer += f"{len(values)}d{size}{str(values)} "
        # answer += "\n"
    except Exception as exc:
        raise RollError("Coding error displaying Dice") from exc

    return answer
