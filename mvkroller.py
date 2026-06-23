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
"""MvKRoller: the two top-level dice rollers, mvkroll and plainroll.

The supporting helpers live in companion modules: rollcommon (shared parsing,
rolling, and display), rollmvkhelpers (MvK rules math), and rollplainhelpers
(plain roll extras). RollError and parse_dice are re-exported here so callers
can keep using ``mvkroller.RollError`` / ``mvkroller.parse_dice``.
"""

import collections
import logging
import re

from rollcommon import (
    NUMBER_EMOJI,
    RollError,
    merge_rolls,
    parse_dice,
    print_dice,
    roll_dice,
)
from rollmvkhelpers import (
    adv_disadv,
    boost_reduce,
    calc_action,
    calc_impact,
    compare_counter,
    crit_fumble,
    crit_success,
    possible_fumble,
    stress_adjust,
)
from rollplainhelpers import parse_math, print_d20_special

logger = logging.getLogger(__name__)

# Tokens that look like dice (``boost d8`` / ``reduce d4``) but name a target for
# a keyword rather than a die to roll; stripped before the pool is parsed.
BOOST_REDUCE_RE = re.compile(r"\b(?:boost|reduce)\s*d[0-9]+", flags=re.IGNORECASE)

# Roll-string modifiers mvkroll understands beyond the dice themselves.
Modifiers = collections.namedtuple(
    "Modifiers",
    "advantage disadvantage overwhelmed staggered counter "
    "action_mod impact_mod boosts reduces burnout",
)


def _impact_modifier(dicestr):
    """Sum ``impact +N`` / ``+N impact`` modifiers and return (total, leftover_text).

    The matched substrings are blanked out of the returned text so the remaining
    +/- numbers can be read as action-total modifiers without double counting.
    """
    impact_mod = 0
    text = dicestr
    # Match "+N impact" (number before) before "impact +N" (number after), so a
    # string like "+2 impact -1" reads as +2 impact and -1 action, not -1 impact.
    for pattern in (r"([+-])\s*([0-9]+)\s*impact", r"impact\s*([+-])\s*([0-9]+)"):
        for sign, num in re.findall(pattern, text, flags=re.IGNORECASE):
            impact_mod += int(sign + num)
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return impact_mod, text


def _parse_modifiers(dicestr):
    """Pull every non-dice modifier mvkroll understands out of the roll string.

    Recognizes advantage/disadvantage, Overwhelmed/Staggered stress, an optional
    counter (``vs N``), flat action-total (`+N`/`-N`) and impact (``impact +N``)
    modifiers, ``boost dN``/``reduce dN``, ``burnout``, and the named effects
    ``unstable`` (-1 action total) and ``burst`` (+2 impact, with disadvantage).
    """
    unstable = bool(re.search(r"\bunstable\b", dicestr, flags=re.IGNORECASE))
    burst = bool(re.search(r"\bburst\b", dicestr, flags=re.IGNORECASE))

    # "disadvantage" contains "advantage", so disadvantage wins when both appear
    # (advantage and disadvantage cancel). Burst is rolled with disadvantage.
    disadvantage = (
        bool(re.search(r"disadvantage", dicestr, flags=re.IGNORECASE)) or burst
    )
    advantage = (
        bool(re.search(r"advantage", dicestr, flags=re.IGNORECASE)) and not disadvantage
    )

    overwhelmed = bool(re.search(r"overwhelmed", dicestr, flags=re.IGNORECASE))
    staggered = bool(re.search(r"staggered", dicestr, flags=re.IGNORECASE))
    match = re.search(r"(?:vs|counter)\s*([0-9]+)", dicestr, flags=re.IGNORECASE)
    counter = int(match.group(1)) if match else None

    impact_mod, leftover = _impact_modifier(dicestr)
    if burst:
        impact_mod += 2
    # Bare +/- numbers left after impact mods are removed adjust the action total.
    action_mod = parse_math(leftover) - (1 if unstable else 0)

    boosts = [
        int(s) for s in re.findall(r"boost\s*d([0-9]+)", dicestr, flags=re.IGNORECASE)
    ]
    reduces = [
        int(s) for s in re.findall(r"reduce\s*d([0-9]+)", dicestr, flags=re.IGNORECASE)
    ]
    burnout = bool(re.search(r"\bburn\s*out\b", dicestr, flags=re.IGNORECASE))

    return Modifiers(
        advantage,
        disadvantage,
        overwhelmed,
        staggered,
        counter,
        action_mod,
        impact_mod,
        boosts,
        reduces,
        burnout,
    )


def _mvk_result_lines(fortunedicerolls, characterdicerolls, mods):
    """Build the crit header and the lines below the dice for an mvkroll.

    Returns ``(crit_header, lines)`` where ``crit_header`` is the top-of-message
    ``### …`` line (or ``""``) and ``lines`` are the breakdown subtext, the bold
    ``Action Total -- Impact`` line, and any reminders/rewards/verdict that follow
    it, in display order.
    """
    fumble_header, characterdicerolls = crit_fumble(
        fortunedicerolls, characterdicerolls
    )
    cs_header, cs_choose = crit_success(fortunedicerolls)
    possible = "" if fumble_header else possible_fumble(fortunedicerolls)

    # Burn Out totals the highest three dice instead of two.
    action_total, action_label, action_from = calc_action(
        fortunedicerolls,
        characterdicerolls,
        keep=3 if mods.burnout else 2,
        modifier=mods.action_mod,
    )
    impact_label, impact_from, min_note = calc_impact(
        fortunedicerolls, characterdicerolls, modifier=mods.impact_mod
    )

    lines = [f"-# {action_from} — {impact_from}"]
    if possible:
        lines.append(possible)
    lines.append(f"**{action_label} — {impact_label}**")
    if min_note:
        lines.append(f"-# {min_note}")
    if cs_choose:
        lines.append(cs_choose)
    if fumble_header:
        lines.append("**Gain 1 inspiration point**")
    verdict = compare_counter(action_total, mods.counter)
    if verdict:
        lines.append(verdict)

    return fumble_header or cs_header, lines


def mvkroll(dicestr: str, prior_rolls=None):
    """Implementation of dice roller that applies MvK rules.

    Returns ``(text, rolls)`` where ``rolls`` is the raw per-size dice rolled
    (captured before the MvK math mutates them). Passing a previous ``rolls`` as
    ``prior_rolls`` reuses those dice and only rolls newly-added ones, so editing
    a roll re-rolls just the additions.
    """

    logger.debug("Roll %s", {dicestr})

    mods = _parse_modifiers(dicestr)

    # Drop "boost dN"/"reduce dN" tokens so their target die isn't read as a die
    # to roll; the boost/reduce itself is applied from mods below.
    dicecounts = parse_dice(BOOST_REDUCE_RE.sub(" ", dicestr))

    # Pool-change notes (set-d20, boost/reduce, stress, advantage/disadvantage)
    # are collected here and rendered together as one quiet subtext line.
    pool_notes = []

    # advantage and disadvantage need _at least_ 2d20; everything else gets 1d20.
    if mods.advantage or mods.disadvantage:
        if dicecounts[20] < 2:
            dicecounts[20] = 2
            pool_notes.append("Set 2d20 for advantage/disadvantage")
    elif dicecounts[20] > 1 or dicecounts[20] == 0:
        dicecounts[20] = 1
        pool_notes.append("No advantage/disadvantage — using 1d20")

    # Pool changes happen before rolling: boost/reduce keywords, then stress
    # (which reduces/scratches the highest remaining character die *type*). Both
    # mutate dicecounts in place; we keep only their note text.
    for note in (
        boost_reduce(dicecounts, mods.boosts, mods.reduces)[0],
        stress_adjust(dicecounts, mods.overwhelmed, mods.staggered)[0],
    ):
        if note:
            pool_notes.append(note)

    if prior_rolls is None:
        dicerolls = roll_dice(dicecounts)
    else:
        dicerolls = merge_rolls(prior_rolls, dicecounts)

    # Snapshot the raw rolls before the MvK math sorts/discards dice, so an edit
    # can reuse them.
    rolls = {size: list(values) for size, values in dicerolls.items()}

    # the d20 is called the "Fortune Die"
    fortunedicerolls = dicerolls[20]
    fortunedicerolls.sort(reverse=True)
    logger.debug("fortune rolls %s", fortunedicerolls)

    adv_note, fortunedicerolls = adv_disadv(
        mods.advantage, mods.disadvantage, dicecounts, dicerolls
    )
    if adv_note:
        pool_notes.append(adv_note)

    dice_text = print_dice(dicerolls).rstrip()

    # dice d4-d12 are called "Character Dice"
    characterdicerolls = [
        val for (key, rollset) in dicerolls.items() if key != 20 for val in rollset
    ]
    characterdicerolls.sort(reverse=True)
    logger.debug("character rolls %s", characterdicerolls)

    if len(characterdicerolls) + len(fortunedicerolls) < 1:
        raise RollError("Not enough dice to roll")

    crit_header, result_lines = _mvk_result_lines(
        fortunedicerolls, characterdicerolls, mods
    )

    # Assemble: a loud crit header on top, supporting detail as quiet -# subtext
    # in the middle, and the headline numbers / rewards / verdict at the bottom.
    lines = []
    if crit_header:
        lines.append(crit_header)
    if pool_notes:
        lines.append("-# " + " — ".join(pool_notes))
    lines.append(f"-# {dice_text}")
    lines.extend(result_lines)

    return "\n".join(lines) + "\n", rolls


def plainroll(dicestr: str, escalation: int = 0, prior_rolls=None):
    """Implementation of dice roller that just rolls some dice for you.

    ``escalation`` is the 13th Age escalation die for the channel. For a single
    d20 (plus any +/- modifiers) it is shown and added to the total as a separate
    "w/Esc" line, but only when it's actually in play (greater than 0).

    Returns ``(text, rolls)``; passing a previous ``rolls`` as ``prior_rolls``
    reuses those dice and only rolls newly-added ones (for edited rolls).
    """

    logger.debug("Roll %s", {dicestr})

    add_amount = parse_math(dicestr)
    logger.debug("add_amount %s", {add_amount})

    dicecounts = parse_dice(dicestr)
    if prior_rolls is None:
        dicerolls = roll_dice(dicecounts)
    else:
        dicerolls = merge_rolls(prior_rolls, dicecounts)

    header, callout = print_d20_special(dicerolls)
    dice_text = print_dice(dicerolls).rstrip()
    total = sum(sum(values) for values in dicerolls.values()) + add_amount

    # A single d20 (modifiers don't count) is the standard 13th Age attack roll,
    # so that's when the escalation die applies.
    single_d20 = dicecounts[20] == 1 and all(
        count == 0 for size, count in dicecounts.items() if size != 20
    )
    show_escalation = single_d20 and escalation > 0

    # A loud crit header on top; the dice and the modifier/escalation details as
    # quiet -# subtext; the bold Total (and escalated total) at the bottom.
    lines = []
    if header:
        lines.append(header)
    lines.append(f"-# {dice_text}")
    if callout:
        lines.append(callout)

    # Combine the flat modifier and the escalation die onto one subtext line.
    if add_amount != 0 and show_escalation:
        lines.append(f"-# Adjustment: {add_amount} + {NUMBER_EMOJI[escalation]}")
    elif add_amount != 0:
        lines.append(f"-# Adjustment: {add_amount}")
    elif show_escalation:
        lines.append(f"-# Esc: {NUMBER_EMOJI[escalation]}")

    lines.append(f"**Total: {total}**")
    if show_escalation:
        lines.append(f"**w/Esc: {total + escalation}**")

    return "\n".join(lines) + "\n", dicerolls
