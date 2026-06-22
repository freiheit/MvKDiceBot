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

import asyncio
import random
import sys
import unittest

import escalationcog
import mvkdicebot
import mvkroller as roller
import rollcog


class TestRoller(unittest.TestCase):
    """Test cases for the mvkroller functions."""

    def test_parser_good(self):
        """Test the parser with valid strings, including some that produce no dice."""
        strings = {
            "": {20: 0, 12: 0, 10: 0, 8: 0, 6: 0, 4: 0},
            "there are no matching dice strings here": {
                20: 0,
                12: 0,
                10: 0,
                8: 0,
                6: 0,
                4: 0,
            },
            "messyd20what?": {20: 1, 12: 0, 10: 0, 8: 0, 6: 0, 4: 0},
            "d20 3d6 5d10": {20: 1, 12: 0, 10: 5, 8: 0, 6: 3, 4: 0},
            "d20 d6 d6 d6 4d10 d10": {20: 1, 12: 0, 10: 5, 8: 0, 6: 3, 4: 0},
            "4d12 1d10 2d4": {20: 0, 12: 4, 10: 1, 8: 0, 6: 0, 4: 2},
            " d4 d6 d8 d12 ": {20: 0, 12: 1, 10: 0, 8: 1, 6: 1, 4: 1},
            "1024d20, 500d4": {20: 1024, 12: 0, 10: 0, 8: 0, 6: 0, 4: 500},
        }
        for dstring, dspec in strings.items():
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

    def test_parse_math(self):
        """+N/-N modifiers are summed, tolerating whitespace after the sign."""
        cases = {
            "": 0,
            "d20": 0,
            "+7": 7,
            "+ 7": 7,
            "+  7": 7,
            "-3": -3,
            "- 3": -3,
            "d20+7": 7,
            "d20 + 7": 7,
            "+5 +2": 7,
            "+5 - 2": 3,
        }
        for dstring, expected in cases.items():
            with self.subTest(dstring=dstring):
                self.assertEqual(roller.parse_math(dstring), expected)

    def test_roller_exception(self):
        """Ensure RollError exceptions carry messages properly."""
        msg = "this is a message"
        try:
            raise roller.RollError(msg)
        except roller.RollError as rex:
            self.assertEqual(rex.getMessage(), msg)

    def test_adv_disadv_good(self):
        """Check behavior of adv_disadv() when given good data."""
        data = [
            [
                True,
                False,
                {20: 2, 10: 1, 6: 2},
                {20: [12, 7], 10: [1], 6: [7, 8]},
                [12],
            ],
            [False, True, {20: 2, 10: 1, 6: 2}, {20: [12, 7], 10: [1], 6: [7, 8]}, [7]],
            [
                False,
                False,
                {20: 2, 10: 1, 6: 2},
                {20: [12, 7], 10: [1], 6: [7, 8]},
                [12, 7],
            ],
            [True, False, {20: 0, 10: 1, 6: 2}, {20: [], 10: [1], 6: [7, 8]}, []],
            [True, False, {20: 1, 10: 1, 6: 2}, {20: [3], 10: [1], 6: [7, 8]}, [3]],
            [False, True, {20: 1, 10: 1, 6: 2}, {20: [3], 10: [1], 6: [7, 8]}, [3]],
        ]
        for adv, dadv, dcount, droll, exp_fortune in data:
            with self.subTest(advantage=adv, disadvantage=dadv, rolls=droll):
                answer, fortune = roller.adv_disadv(adv, dadv, dcount, droll)
                self.assertEqual(fortune, exp_fortune)
                self.assertIsNotNone(answer)

    def test_adv_disadv_bad(self):
        """Force adv_disadv to fail with bad data and ensure RollError is raised."""
        with self.assertRaises(roller.RollError):
            roller.adv_disadv(True, False, {20: 2}, {20: "not an array"})

    def test_roll_dice(self):
        """Check the dice roller with a deterministic random source."""
        dataset = [
            [{}, {20: [], 12: [], 10: [], 8: [], 6: [], 4: []}],
            [
                {20: 2, 6: 5},
                {20: [9, 5], 12: [], 10: [], 8: [], 6: [2, 2, 5, 2, 3], 4: []},
            ],
            [
                {20: 1, 12: 1, 10: 1, 8: 1, 6: 1, 4: 1},
                {20: [9], 12: [3], 10: [2], 8: [2], 6: [5], 4: [2]},
            ],
        ]
        for dcount, result in dataset:
            with self.subTest(dice_count=dcount):
                self.assertEqual(roller.roll_dice(dcount, random.Random(99)), result)

        # Without an explicit source we only check that we got a value.
        the_rolls = roller.roll_dice({20: 1})
        self.assertGreater(len(the_rolls[20]), 0)

    def test_roll_dice_exc(self):
        """Test attempts to roll dice with a bad dice count."""
        dataset = [
            {20: "nope!"},
            {"8": 1},
            {8: 12, "umbridge": "sucks"},
        ]
        for dcount in dataset:
            with self.subTest(dice_count=dcount), self.assertRaises(roller.RollError):
                roller.roll_dice(dcount)

    def test_print_dice(self):
        """Print some valid die rolls."""
        dataset = [
            [{}, "Dice: "],
            [{20: [5, 12]}, "Dice: 2d20[5, 12] "],
            [
                {20: [], 12: [1, 12], 8: [1, 2, 3, 4], 4: [3, 2]},
                "Dice: 2d12[1, 12] 4d8[1, 2, 3, 4] 2d4[3, 2] ",
            ],
        ]
        for rolls, result in dataset:
            with self.subTest(rolls=rolls):
                self.assertEqual(roller.print_dice(rolls), result)

    def test_print_dice_exc(self):
        """print_dice raises when the input is not a dictionary."""
        dataset = [
            [20, 1],
            "nobody",
            99,
        ]
        for bad_roll in dataset:
            with self.subTest(bad_roll=bad_roll), self.assertRaises(roller.RollError):
                roller.print_dice(bad_roll)

    def test_calc_action(self):
        """Ensure actions are tallied properly (only the highest fortune die counts)."""
        dataset = [
            [[1, 20], [2, 4, 6, 8], "**Action Total: 28** [20, 8]\n"],
            [[20, 1], [8, 6, 4, 2], "**Action Total: 28** [20, 8]\n"],
            [[11, 13, 5], [8, 6, 4, 2], "**Action Total: 21** [13, 8]\n"],
            [[6, 7, 8], [9, 10, 11, 12], "**Action Total: 23** [12, 11]\n"],
        ]
        for fdice, cdice, answer in dataset:
            with self.subTest(dice=[fdice, cdice]):
                self.assertEqual(roller.calc_action(fdice, cdice), answer)

    def test_calc_action_exc(self):
        """Give calc_action() some bad data."""
        dataset = [
            [None, None],
            ["boopsie", "whoopsie"],
            [12, 99],
            [[1, 2], "grrrrr"],
            ["grrrr", [1, 2]],
        ]
        for fdice, cdice in dataset:
            with self.subTest(dice=[fdice, cdice]), self.assertRaises(roller.RollError):
                roller.calc_action(fdice, cdice)


class TestBotCommands(unittest.TestCase):
    """Test that the bot exposes both prefix and slash (app) commands.

    The commands live in cogs that setup_hook loads as extensions at startup;
    here we load those extensions explicitly (the bot never connects to Discord,
    so the live sync can't be unit-tested -- its runtime confirmation is the
    "Synced N application command(s)" log line emitted on startup).
    """

    @classmethod
    def setUpClass(cls):
        """Load the command cogs the same way setup_hook would."""

        async def _load():
            for extension in mvkdicebot.EXTENSIONS:
                if extension not in mvkdicebot.bot.extensions:
                    await mvkdicebot.bot.load_extension(extension)

        asyncio.run(_load())

    def test_prefix_commands_registered(self):
        """The primary command names resolve as text/prefix commands."""
        for name in ("mvkroll", "plainroll"):
            with self.subTest(name=name):
                self.assertIsNotNone(mvkdicebot.bot.get_command(name))

    def test_aliases_still_work(self):
        """The legacy aliases still resolve to their commands."""
        aliases = {
            "r": "mvkroll",
            "roll": "mvkroll",
            "p": "plainroll",
            "justroll": "plainroll",
            "esc": "escalation",
            "e": "escalation",
        }
        for alias, target in aliases.items():
            with self.subTest(alias=alias):
                command = mvkdicebot.bot.get_command(alias)
                self.assertIsNotNone(command)
                self.assertEqual(command.name, target)

    def test_app_commands_in_tree(self):
        """The commands (incl. /r, /p, /help) are present in the application command tree."""
        app_names = {cmd.name for cmd in mvkdicebot.bot.tree.get_commands()}
        for name in ("mvkroll", "plainroll", "help", "r", "p", "escalation", "esc"):
            with self.subTest(name=name):
                self.assertIn(name, app_names)

    def test_help_command_routes_through_context(self):
        """The help command sends through the context so /help can reuse it."""
        # Reference the class via the loaded extension module: load_extension
        # replaces sys.modules["helpcog"], so a top-level import would be stale.
        help_cls = sys.modules["helpcog"].HybridHelpCommand
        self.assertIsInstance(mvkdicebot.bot.help_command, help_cls)

    def test_setup_hook_is_callable(self):
        """The startup sync hook is wired up."""
        self.assertTrue(callable(mvkdicebot.bot.setup_hook))


class TestRollEcho(unittest.TestCase):
    """Test the optional input echo used by the slash commands."""

    @staticmethod
    def _capture():
        """Return (captured_list, async send) that records what was sent."""
        captured = []

        async def send(msg):
            captured.append(msg)

        return captured, send

    def test_echo_prepends_input(self):
        """echo_input prepends the roll string as a '-# ' subtext line."""
        captured, send = self._capture()
        asyncio.run(
            rollcog._do_roll(send, lambda s: "RESULT", "d20 +7", echo_input=True)
        )
        self.assertEqual(captured, ["> -# `d20 +7`\nRESULT"])

    def test_no_echo_by_default(self):
        """Without echo_input the output is unchanged (the text-command case)."""
        captured, send = self._capture()
        asyncio.run(rollcog._do_roll(send, lambda s: "RESULT", "d20 +7"))
        self.assertEqual(captured, ["RESULT"])

    def test_echo_on_error(self):
        """The echo line is also prepended to a RollError message, then re-raised."""
        captured, send = self._capture()

        def boom(_):
            raise roller.RollError("bad dice")

        with self.assertRaises(roller.RollError):
            asyncio.run(rollcog._do_roll(send, boom, "d99", echo_input=True))
        self.assertEqual(captured, ["> -# `d99`\nbad dice"])


class TestEscalation(unittest.TestCase):
    """Test the escalation-die value logic and the inactivity expiry."""

    def test_next_value_increment_caps(self):
        """+1/up/next increment but never exceed the maximum."""
        for action in ("+", "+1", "up", "next", "advance"):
            with self.subTest(action=action):
                self.assertEqual(escalationcog.next_value(0, action), 1)
                self.assertEqual(escalationcog.next_value(3, action), 4)
                self.assertEqual(
                    escalationcog.next_value(escalationcog.MAX_VALUE, action),
                    escalationcog.MAX_VALUE,
                )

    def test_next_value_decrement_floors(self):
        """-1/down/back decrement but never go below 0."""
        for action in ("-", "-1", "down", "back"):
            with self.subTest(action=action):
                self.assertEqual(escalationcog.next_value(3, action), 2)
                self.assertEqual(escalationcog.next_value(0, action), 0)

    def test_next_value_reset_and_set(self):
        """reset/new/end go to 0; a bare number sets directly."""
        for action in ("reset", "new", "end", "0"):
            with self.subTest(action=action):
                self.assertEqual(escalationcog.next_value(5, action), 0)
        self.assertEqual(escalationcog.next_value(0, "3"), 3)
        self.assertEqual(escalationcog.next_value(2, "6"), 6)

    def test_next_value_bad_input(self):
        """Out-of-range or unrecognized actions raise ValueError."""
        for action in ("7", "99", "+2", "banana", "-3"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                escalationcog.next_value(0, action)

    def test_tracker_per_key_isolation(self):
        """Different channels track independent values."""
        tracker = escalationcog.EscalationTracker(now=lambda: 0.0)
        tracker.set("a", 3)
        tracker.set("b", 5)
        self.assertEqual(tracker.get("a"), 3)
        self.assertEqual(tracker.get("b"), 5)
        self.assertEqual(tracker.get("never-set"), 0)

    def test_tracker_expiry(self):
        """A value lapses back to 0 once it has gone untouched past EXPIRY."""
        clock = {"t": 1000.0}
        tracker = escalationcog.EscalationTracker(now=lambda: clock["t"], expiry=100)
        tracker.set("chan", 4)
        clock["t"] += 50  # still fresh
        self.assertEqual(tracker.get("chan"), 4)
        clock["t"] += 100  # now 150s since set, past the 100s expiry
        self.assertEqual(tracker.get("chan"), 0)

    def test_format_value(self):
        """Formatting uses a header, a keycap emoji, and a subtext detail line."""
        zero = escalationcog.format_value(0)
        self.assertIn("## Escalation Die Is", zero)
        self.assertIn(":zero:", zero)
        self.assertIn("No bonus yet", zero)

        three = escalationcog.format_value(3)
        self.assertIn(":three:", three)
        self.assertIn("+3", three)

        maxed = escalationcog.format_value(escalationcog.MAX_VALUE)
        self.assertIn(":six:", maxed)
        self.assertIn("maximum", maxed)


if __name__ == "__main__":
    unittest.main()
