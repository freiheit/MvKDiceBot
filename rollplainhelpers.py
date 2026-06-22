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

from rollcommon import RollError


def print_d20_special(dicerolls):
    """Checks for special d20 rules and adds stuff for any special stuff"""
    answer = ""
    try:
        for size, values in dicerolls.items():
            if len(values) == 1 and size == 20:
                if values[0] == 1:
                    answer += "\n1 is **Crit Fumble/Fail**"
                elif values[0] == 20:
                    answer += "\n20 is **Crit Success**"
                elif values[0] % 2 == 0:
                    answer += " (_Even_)"
                else:
                    answer += " (_Odd_)"

                if values[0] == 2:  # separate because also even
                    answer += "\n_Two-Weapon Hit?_"

    except Exception as exc:
        raise RollError("Coding error displaying Dice") from exc

    return answer


def parse_math(dicestr: str):
    """Look for +N and -N things to get a total change"""

    pattern_math = re.compile(r"([+-][0-9]+)")

    amount = 0

    for addstr in re.findall(pattern_math, dicestr):
        amount += int(addstr)

    return amount
