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

# The next-smaller size a character die reduces to (the fortune d20 is never
# reduced). Reducing a d4 drops it from the pool entirely.
_SMALLER_SIZE = {12: 10, 10: 8, 8: 6, 6: 4, 4: None}


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
    """Compute the action total, using the highest two rolls. Up to one fortune die may be used.

    Returns ``(answer, action_total)`` so callers can compare the numeric total
    against an opposing counter total.
    """
    try:
        action_dice = sorted(fortunedicerolls, reverse=True)[:1]
        action_dice += characterdicerolls
        action_dice.sort(reverse=True)
        action_dice = action_dice[:2]
        action_total = sum(action_dice)
        answer = f"**Action Total: {str(action_total)}** {str(action_dice)}\n"
    except Exception as exc:
        raise RollError(
            "Coding error flattening dice rolls and creating total."
        ) from exc
    return answer, action_total


def calc_impact(fortunedicerolls, characterdicerolls):
    """Calculate the impact total"""
    try:
        # die results of 10 or higher on a d10 or 12 give two impact. It doesn't happen on a d20.
        fortune_high = fortunedicerolls[0] >= 4
        fortuneimpact = 1 if fortune_high else 0
        doublecharacterimpact = sum(2 for p in characterdicerolls if p >= 10)
        characterimpact = sum(1 for p in characterdicerolls if 4 <= p < 10)
        raw = fortuneimpact + doublecharacterimpact + characterimpact
        # Minimum impact of 1, but only when the fortune die rolled 4+ (even a
        # countered action still accomplishes something). With no 4+ fortune die
        # and no qualifying character dice the impact is genuinely 0.
        impact = max(raw, 1) if fortune_high else raw
        answer = f"**Impact: {impact}** "
        answer += (
            f"(fortune={fortuneimpact} 2x={doublecharacterimpact} 1x={characterimpact})"
        )
        # When that lone point comes only from the fortune die, it's the minimum
        # impact you keep even if the action is countered -- worth spelling out.
        if (
            impact == 1
            and fortuneimpact == 1
            and not doublecharacterimpact
            and not characterimpact
        ):
            answer += "\n-# Minimum impact 1 from the fortune die (even if countered)."
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


def crit_success(fortunedicerolls):
    """A 20 on the fortune die used for the total is a critical success.

    ``fortunedicerolls`` is sorted descending and (after advantage/disadvantage)
    holds the single kept die, so index 0 is the die used for the action total.
    A critical success and a critical fumble can't both happen on that one die.
    """
    if fortunedicerolls and fortunedicerolls[0] == 20:
        return (
            "**Critical Success**\n"
            "Choose: increase your Impact by 2, or gain 1 inspiration point.\n"
        )
    return ""


def compare_counter(action_total, counter):
    """Compare the action total to an optional counter total (None = skip).

    Per the rules, the action succeeds unless the counter total is *higher*, so
    a tie is a success. An unsuccessful action can't inflict stress, but the
    actor still gets their minimum impact, so we say so rather than zeroing it.
    """
    if counter is None:
        return ""
    if action_total >= counter:
        return f"**Success!** (Action {action_total} vs Counter {counter})\n"
    return (
        f"**Failure** (Action {action_total} vs Counter {counter})\n"
        "-# Countered: cannot inflict stress; minimum impact still applies.\n"
    )


def stress_adjust(dicecounts, overwhelmed, staggered):
    """Apply Overwhelmed/Staggered stress to the dice pool *before* it is rolled.

    Stress targets the largest character die in the pool (the fortune d20 is
    never reduced). Overwhelmed OR Staggered reduces that die one size, so it is
    then rolled at the smaller size (a d4 is removed from the pool entirely);
    Overwhelmed AND Staggered scratches it (removed before any roll, per the
    rulebook's "scratch the highest die in your pool before making any roll").
    Mutates and returns ``(answer, dicecounts)``; the answer is empty when
    neither condition applies.
    """
    if not (overwhelmed or staggered):
        return "", dicecounts

    try:
        size = next((s for s in (12, 10, 8, 6, 4) if dicecounts.get(s, 0) > 0), None)
        if size is None:
            return "**Stress**\n-# No character dice to reduce.\n", dicecounts

        dicecounts[size] -= 1

        if overwhelmed and staggered:
            return (
                f"**Stress: Overwhelmed & Staggered**\n*Scratched highest die: d{size}*\n",
                dicecounts,
            )

        smaller = _SMALLER_SIZE[size]
        if smaller is None:
            detail = f"d{size} → removed"
        else:
            dicecounts[smaller] += 1
            detail = f"d{size} → d{smaller}"
        return (
            f"**Stress: Overwhelmed/Staggered**\n*Reduced highest die: {detail}*\n",
            dicecounts,
        )
    except Exception as exc:
        raise RollError("Coding error applying stress.") from exc
