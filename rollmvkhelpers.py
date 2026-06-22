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
"""Helpers specific to the MvK ruleset roller (mvkroll)."""

import logging

from rollcommon import RollError

logger = logging.getLogger(__name__)


def adv_disadv(advantage, disadvantage, dicecounts, dicerolls):
    """Perform extra work when rolling with advantage or disadvantage"""
    answer = ""
    fortunedicerolls = dicerolls[20]

    try:
        if (advantage or disadvantage) and len(fortunedicerolls):
            logger.debug("Dicecounts %s", dicecounts)
            logger.debug("Dicerolls %s", dicerolls)
            answer += "Original d20s: "
            answer += f"{len(fortunedicerolls)}d20{str(fortunedicerolls)} -- "
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
    """Compute the action total, using the highest two rolls. Up to one fortune die may be used."""
    try:
        action_dice = sorted(fortunedicerolls, reverse=True)[:1]
        action_dice += characterdicerolls
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


def possible_fumble(fortunedicerolls):
    """
    You also critically fumble if your action is successfully countered
    and you roll a 1-3 on the d20
    """
    answer = ""
    if fortunedicerolls[0] <= 3:
        answer += "**Possible Critical Fumble**\n"
        answer += (
            "If your action is successfully countered, gain 1 inspiration point.\n"
        )
    return answer
