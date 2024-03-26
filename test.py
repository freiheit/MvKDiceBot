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
"""Test module for MvKDiceBot"""

import random
import unittest
import mvkroller as roller

class TestRoller(unittest.TestCase):
    """Test cases for the mvkroller functions."""

    def test_roller_exception(self):
        """Ensure RollError exceptions carry messages properly"""
        msg = "this is a message"
        try:
            raise roller.RollError(msg)
        except roller.RollError as rex:
            self.assertEqual(rex.getMessage(), msg)

    def test_parser_good(self):
        """Test the parser with valid strings, including some that produce no dice."""
        strings = {
            "": {20:0, 12:0, 10:0, 8:0, 6:0, 4:0},
            "there are no matching dice strings here": {20:0, 12:0, 10:0, 8:0, 6:0, 4:0},
            "messyd20what?": {20:1, 12:0, 10:0, 8:0, 6:0, 4:0},
            "d20 3d6 5d10": {20:1, 12:0, 10:5, 8:0, 6:3, 4:0},
            "d20 d6 d6 d6 4d10 d10": {20:1, 12:0, 10:5, 8:0, 6:3, 4:0},
            "4d12 1d10 2d4": {20:0, 12:4, 10:1, 8:0, 6:0, 4:2},
            " d4 d6 d8 d12 ": {20:0, 12:1, 10:0, 8:1, 6:1, 4:1},
            "1024d20, 500d4": {20:1024, 12:0, 10:0, 8:0, 6:0, 4:500},
        }
        for (dstring, dspec) in strings.items():
            with self.subTest(dstring=dstring):
                self.assertEqual(roller.parse_dice(dstring), dspec)

    def test_parser_bad(self):
        """Ensure the parser will throw exceptions when bad dice sizes are given."""
        strings = [
            "50d3nothing",
            "50d17",
            "1d20 2d7",
        ]
        for dstring in strings:
            with self.subTest(dstring=dstring), self.assertRaises(roller.RollError):
                roller.parse_dice(dstring)

    def test_addadv_good(self):
        """Check behavior of adv_disadv() when given good data."""
        data = [
            [True, False, {20:2, 10:1, 6:2}, {20:[12,7], 10:[1], 6:[7,8]}, [12]],
            [False, True, {20:2, 10:1, 6:2}, {20:[12,7], 10:[1], 6:[7,8]}, [7]],
            [False, False, {20:2, 10:1, 6:2}, {20:[12,7], 10:[1], 6:[7,8]}, [12, 7]],
            [True, False, {20:0, 10:1, 6:2}, {20:[], 10:[1], 6:[7,8]}, []],
            [True, False, {20:1, 10:1, 6:2}, {20:[3], 10:[1], 6:[7,8]}, [3]],
            [False, True, {20:1, 10:1, 6:2}, {20:[3], 10:[1], 6:[7,8]}, [3]],
        ]
        for (adv, dadv, dcount, droll, exp_fortune) in data:
            with self.subTest():
                answer, fortune = roller.adv_disadv(adv, dadv, dcount, droll)
                self.assertEqual(fortune, exp_fortune)
                self.assertIsNotNone(answer)

    def test_addadv_bad(self):
        """Force adv_disadv to fail because of bad data. Ensure RollError is raised."""
        with self.assertRaises(roller.RollError):
            roller.adv_disadv(True, False, {20:2}, {20:"not an array"})

    def test_roll_dice(self):
        """Check the dice roller!"""
        dataset = [
            [{}, {20:[], 12:[], 10:[], 8:[], 6:[], 4:[]}],
            [{20:2, 6:5}, {20:[9,5], 12:[], 10:[], 8:[], 6:[2,2,5,2,3], 4:[]}],
            [{20:1, 12:1, 10:1, 8:1, 6:1, 4:1}, {20:[9], 12:[3], 10:[2], 8:[2], 6:[5], 4:[2]}],
        ]
        for (dcount, result) in dataset:
            with self.subTest():
                rsource = random.Random(99)
                self.assertEqual(roller.roll_dice(dcount, rsource), result)

        # Same as dataset[0], but without the explicit random source
        # Only check that we got a value. We don't care what the value was.
        the_rolls = roller.roll_dice({20:1})
        self.assertGreater(len(the_rolls[20]), 0)

    def test_roll_dice_exc(self):
        """Test attempts to roll dice with a bad dice count."""
        dataset = [
            {20:"nope!"},
            {"8":1},
            {8:12, "umbridge":"sucks"},
        ]
        for dcount in dataset:
            with self.subTest(dice_count=dcount), self.assertRaises(roller.RollError):
                roller.roll_dice(dcount)

if __name__ == "__main__":
    unittest.main()
