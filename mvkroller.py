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
"""MvKRoller: Dice roller for the MvKDiceBot"""

import functools
import logging
import random
import re

logger = logging.getLogger(__name__)


class RollError(Exception):
    """Boring Exception Class"""

    message = ""

    def __init__(self, msg):
        self.message = msg

    # pylint: disable=invalid-name
    def getMessage(self):
        """return this exception's message"""
        return self.message


@functools.cache
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


def roll_dice(dicecounts, cheat=False):
    """Returns a dictionary of dieSize => rolls[]"""
    dicerolls = {
        20: [],
        12: [],
        10: [],
        8: [],
        6: [],
        4: [],
    }

    try:
        for size, num in dicecounts.items():
            if num > 0:
                # pylint: disable=unused-variable
                if cheat:
                    dicerolls[size] = [size for idx in range(0, num)]
                else:
                    dicerolls[size] = [random.SystemRandom().randint(1, size) for idx in range(0, num)]
    except Exception as exc:
        raise RollError("Exception while rolling dice.") from exc

    return dicerolls


def print_dice(dicerolls):
    "Creates a string rep of the rolled dice"
    answer = "Dice: "
    try:
        for size, values in dicerolls.items():
            if len(values) > 0:
                answer += f"{len(values)}d{size}{ str(values)} "
        answer += "\n"
    except Exception as exc:
        raise RollError("Coding error displaying Dice") from exc

    return answer


def adv_disadv(advantage, disadvantage, dicecounts, dicerolls):
    """Perform extra work when rolling with advantage or disadvantage"""
    answer = ""
    fortunedicerolls = dicerolls[20]

    try:
        if advantage or disadvantage:
            logger.debug("Dicecounts %s", dicecounts)
            logger.debug("Dicerolls %s", dicerolls)
            answer += "Original d20s: "
            answer += f"{len(fortunedicerolls)}d20{ str(fortunedicerolls)} -- "
            if advantage:
                answer += "_Applying advantage_\n\n"
                dicerolls[20].sort(reverse=True)
                logger.debug("Advantage rolls %s", dicerolls[20])
            if disadvantage:
                answer += "_Applying disadvantage_\n\n"
                dicerolls[20].sort()
                logger.debug("Disadvantage rolls %s", dicerolls[20])
            dicerolls[20] = [dicerolls[20][0]]
    except Exception as exc:
        raise RollError("Coding error calculating advantage or disadvantage.") from exc

    return answer, dicerolls[20]


def calc_action(fortunedicerolls, characterdicerolls):
    """Compute the action total, using up to one d20 and the highest character die roll."""
    try:
        action_dice = fortunedicerolls + characterdicerolls
        action_dice.sort(reverse=True)
        action_dice = action_dice[:2]
        answer = f"**Action Total: {str(sum(action_dice))}** {str(action_dice)}\n"
    except Exception as exc:
        raise RollError(
            "Coding error flattening dice rolls and creating total."
        ) from exc
    return answer


def calc_impact(fortunedicerolls, characterdicerolls):
    """Calculate the impact total"""
    try:
        # die results of 10 or higher on a d10 or 12 give two impact. It doesn't happen on a d20.
        fortuneimpact = 1 if fortunedicerolls[0] >= 4 else 0
        doublecharacterimpact = sum(2 for p in characterdicerolls if p >= 10)
        characterimpact = sum(1 for p in characterdicerolls if 4 <= p < 10)
        impact = fortuneimpact + doublecharacterimpact + characterimpact
        impact = max(impact, 1)
        answer = f"**Impact: {impact}** "
        answer += (
            f"(fortune={fortuneimpact} 2x={doublecharacterimpact} 1x={characterimpact})"
        )
    except Exception as exc:
        raise RollError("Coding error calculating Impact") from exc
    return answer


def crit_fumble(fortunedicerolls, characterdicerolls):
    """Check if we had a critical fumble. If so, add output and discard lowest non-1 die"""
    answer = ""
    newdicerolls = characterdicerolls
    if fortunedicerolls[0] == 1:
        answer += "**Critical Fumble**\n"
        characterdicerolls.sort()
        newdicerolls = []
        scratched = False
        for i in characterdicerolls:
            if scratched:
                newdicerolls.append(i)
            elif i == 1:
                newdicerolls.append(i)
            else:
                scratched = True
                answer += f"*Scratched {i}*\n"
                # no append because scratching this die

        answer += "**Gain 1 inspiration point**\n"
        answer += f"New character dice: {newdicerolls}\n"
    return answer, newdicerolls


def mvkroll(dicestr: str):
    """Implementation of dice roller that applies MvK rules."""

    logger.debug("Roll %s", {dicestr})

    answer = ""
    cheat = False
    advantage = False
    disadvantage = False

    if re.search(r"disadvantage", dicestr, flags=re.IGNORECASE):
        disadvantage = True
    elif re.search(r"advantage", dicestr, flags=re.IGNORECASE):
        advantage = True

    if re.search(r"cheat", dicestr, flags=re.IGNORECASE):
        cheat = True

    dicecounts = parse_dice(dicestr)

    # advantage and disadvantage need _at least_ 2d20
    # everything else only gets 1d20
    if advantage or disadvantage:
        if dicecounts[20] < 2:
            dicecounts[20] = 2
            answer += "_Setting 2d20 for advantage/disadvantage_\n"
    elif dicecounts[20] > 1 or dicecounts[20] == 0:
        dicecounts[20] = 1
        answer += "_No advantage/disadvantage, setting 1d20_\n"

    dicerolls = roll_dice(dicecounts, cheat)

    # the d20 is called the "Fortune Die"
    fortunedicerolls = dicerolls[20]
    fortunedicerolls.sort(reverse=True)
    logger.debug("fortune rolls %s", fortunedicerolls)

    # dice d4-d12 are called "Character Dice"
    # Grab all the values from all the rolls that weren't d20s
    characterdicerolls = [
        val for (key, rollset) in dicerolls.items() if key != 20 for val in rollset
    ]
    characterdicerolls.sort(reverse=True)
    logger.debug("character rolls %s", characterdicerolls)

    if len(characterdicerolls) + len(fortunedicerolls) < 1:
        raise RollError("Not enough dice to roll")

    adv_disadv_answer, fortunedicerolls = adv_disadv(
        advantage, disadvantage, dicecounts, dicerolls
    )
    answer += adv_disadv_answer

    answer += print_dice(dicerolls)

    fumble_answer, characterdicerolls = crit_fumble(
        fortunedicerolls, characterdicerolls
    )
    answer += fumble_answer

    answer += calc_action(fortunedicerolls, characterdicerolls)

    answer += calc_impact(fortunedicerolls, characterdicerolls)

    if cheat:
        answer = "\n# Cheating #\n" + answer + "\n# Cheater #\n"

    return answer


def plainroll(dicestr: str):
    """Implementation of dice roller that just rolls some dice for you."""

    logger.debug("Roll %s", {dicestr})

    answer = ""
    cheat = False

    dicecounts = parse_dice(dicestr)
    dicerolls = roll_dice(dicecounts, cheat)

    answer += print_dice(dicerolls)

    return answer
