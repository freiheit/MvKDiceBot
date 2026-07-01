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
"""Helpers specific to the plain dice roller (plainroll)."""

import re

from rollcommon import _DICE_RE, RollError


def print_d20_special(dicerolls):
    """Check a single d20 for special results.

    Returns ``(header, callout)``: ``header`` is a top-of-message ``### 🎯/💥``
    crit line for a natural 20/1 (empty otherwise); ``callout`` is the even/odd
    (and Two-Weapon on a 2) note shown on its own line after the dice (empty for
    a crit, or when this isn't a lone d20). Both empty when there's no single d20.
    """
    header = ""
    callout = ""
    try:
        values = dicerolls.get(20, [])
        only_d20 = len(values) == 1 and all(
            len(rolls) == 0 for size, rolls in dicerolls.items() if size != 20
        )
        if only_d20:
            value = values[0]
            if value == 20:
                header = "### 🎯 Critical Success"
            elif value == 1:
                header = "### 💥 Critical Fumble"
            elif value % 2 == 0:
                callout = "(Even)"
            else:
                callout = "(Odd)"

            if value == 2:  # separate because also even
                callout += " — Two-Weapon Hit?"
    except Exception as exc:
        raise RollError("Coding error displaying Dice") from exc

    return header, callout


def parse_math(dicestr: str):
    """Look for +N and -N things to get a total change.

    Whitespace between the sign and the number is allowed, so '+7', '+ 7', and
    '+  7' are all equivalent.

    Dice terms are blanked out first (via the same regex ``parse_dice`` uses) so a
    die-count like the ``2`` in ``+2d8`` is never mistaken for a ``+2`` modifier;
    ``1d20+1d6+2d8`` is the pool ``1d20 1d6 2d8`` with no adjustment.
    """

    without_dice = _DICE_RE.sub(" ", dicestr)

    pattern_math = re.compile(r"([+-])\s*([0-9]+)")

    amount = 0

    for sign, num in re.findall(pattern_math, without_dice):
        amount += int(sign + num)

    return amount
