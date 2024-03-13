#!.venv/bin/python3
# MvKRoller: Dice roller for the MvK Dice Bot
# Copyright (C) 2023  Eric Eisenhart
# edited by CJ Holmes
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
"""MvKRoller: Dice roller for the MvKDiceBot"""

import logging
import os
import random
import re
import warnings

logger = logging.getLogger(__name__)

class RollError(Exception):
    """Boring Exception Class"""

    # pylint: disable=unnecessary-pass
    pass

def roll(dicestr: str):
  """Rolls a pool of dice in NdN format.
  Example: '?roll 1d20 2d10 d8 2d6'

  Add 'advantage' to discard lowest d20.
  Add 'disadvantage' to discard highest d20.
  Example: '?roll 2d20 2d10 advantage'
  Example: '?roll 2d20 2d10 disadvantage'

  Ignores anything extra it doesn't understand.
  """
  # pylint: disable=logging-fstring-interpolation
  # pylint: disable=consider-using-dict-items
  # pylint: disable=too-many-locals
  # pylint: disable=too-many-branches
  # pylint: disable=too-many-statements
  # pylint: disable=too-many-nested-blocks
  # pylint: disable=line-too-long

  logger.debug(f"Roll {dicestr}")

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

  # types of dice we're looking for:
  dicecounts = {
      20: 0,
      12: 0,
      10: 0,
      8: 0,
      6: 0,
      4: 0,
  }

  dicerolls = {
      20: [],
      12: [],
      10: [],
      8: [],
      6: [],
      4: [],
  }

  # dice d4-d12 are called "Character Dice" and the d20 is called the "Fortune Die"
  characterdicerolls = []  # non-d20 dice
  fortunedicerolls = []  # d20s

  pattern_ndn = re.compile(r"([0-9]*) *[dD]([0-9]+)")

  try:
      for count, size in re.findall(pattern_ndn, dicestr):
          logger.debug(f"Roll count={count} size={size}")
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
      raise RollError("Error parsing dice rolls. No NdN?") from exc

  try:
      for size in dicecounts:
          if dicecounts[size] > 0:
              # logger.debug(f"rolling: d{size}={dicecounts[size]}")
              dicerolls[size] = []
              # pylint: disable=unused-variable
              for i in range(0, dicecounts[size]):
                  if cheat:
                      result = size
                  else:
                      result = random.randint(1, size)
                  dicerolls[size].append(result)
                  if size == 20:
                      fortunedicerolls.append(result)
                  else:
                      characterdicerolls.append(result)
  except Exception:
      raise RollError("Coding error rolling dice.")

  fortunedicerolls.sort(reverse=True)
  characterdicerolls.sort(reverse=True)

  try:
      if (
          len(
              dicerolls[20]
              + dicerolls[12]
              + dicerolls[10]
              + dicerolls[8]
              + dicerolls[6]
              + dicerolls[4]
          )
          > 0
      ):
          if cheat:
              answer += "# Cheating\n"

          try:
              if advantage or disadvantage:
                  logger.debug(f"Dicecounts {dicecounts}")
                  logger.debug(f"Dicerolls {dicerolls}")
                  if dicecounts[20] >= 2 and len(dicerolls[20]) >= 2:
                      answer += "Original d20s: "
                      answer += f"{len(dicerolls[20])}d20{ str(dicerolls[20])} -- "
                      if advantage:
                          answer += "Applying _advantage_...\n\n"
                          dicerolls[20].sort(reverse=True)
                          logger.debug(f"Advantage rolls {dicerolls[20]}")
                      if disadvantage:
                          answer += "Applying _disadvantage_...\n\n"
                          dicerolls[20].sort()
                          logger.debug(f"Disadvantage rolls {dicerolls[20]}")
                      retained_d20 = dicerolls[20][0]
                      dicerolls[20] = [retained_d20]
                  else:
                      answer += (
                          "## Advantage and Disadvantage require 2 or more d20s\n"
                      )
                      answer += "Rolling normally...\n\n"
                      advantage = False
                      disadvantage = False
          except Exception as exc:
              raise RollError("Coding error calculating advantage or disadvantage.") from exc

          try:
              answer += "Dice: "
              for size in dicerolls:
                  if len(dicerolls[size]) > 0:
                      answer += (
                          f"{len(dicerolls[size])}d{size}{ str(dicerolls[size])} "
                      )
              answer += "\n"
          except Exception as exc:
              raise RollError("Coding error displaying Dice") from exc

          try:
              flatdicerolls = (
                  dicerolls[20]
                  + dicerolls[12]
                  + dicerolls[10]
                  + dicerolls[8]
                  + dicerolls[6]
                  + dicerolls[4]
              )
              flatdicerolls.sort(reverse=True)
          except Exception as exc:
              raise RollError(
                  "Coding error flattening dice rolls into single sorted list."
              ) from exc

          try:
              action_dice = flatdicerolls[:2]
              action_total = sum(action_dice)
              answer += f"**Action Total: {str(action_total)}** {str(action_dice)}\n"
          except Exception as exc:
              raise RollError("Coding error calculating Action Total.") from exc

          try:
              # die results of 10 or higher on a d10 or 12 give two impact. It doesn't happen on a d20.
              fortuneimpact = 1 if dicerolls[20][0] >= 4 else 0
              doublecharacterimpact = sum(2 for p in characterdicerolls if p >= 10)
              characterimpact = sum(1 for p in characterdicerolls if 4 <= p < 10)
              impact = fortuneimpact + doublecharacterimpact + characterimpact
              impact = max(impact, 1)
              answer += f"**Impact: {impact}** "
              answer += f"(fortune={fortuneimpact} 2x={doublecharacterimpact} 1x={characterimpact})"
          except Exception as exc:
              raise RollError("Coding error calculating Impact")

          if cheat:
              answer += "\n# Cheating"

      else:
          answer += f"No valid NdNs found in '{dicestr}'"
  except Exception as exc:
      raise RollError("Coding error calculating totals.") from exc
  return answer
