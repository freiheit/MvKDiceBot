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

import unittest
import mvkroller as roller

class TestRoller(unittest.TestCase):
    """Test cases for the mvkroller functions."""

    def test_parser_good(self):
        """Test the parser with valid strings, including some that produce no dice."""
        strings = {
            "": {20:0, 12:0, 10:0, 8:0, 6:0, 4:0},
            "there are no matching dice strings here": {20:0, 12:0, 10:0, 8:0, 6:0, 4:0},
            "messyd20what?": {20:1, 12:0, 10:0, 8:0, 6:0, 4:0},
            "d20 3d6 5d10": {20:1, 12:0, 10:5, 8:0, 6:3, 4:0},
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

if __name__ == "__main__":
    unittest.main()
