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
"""Per-guild command-prefix storage for MvKDiceBot.

Prefixes are cached in memory (read once at startup) and written through to a
sqlite database whenever they change. The bot always also responds to @-mentions
and to its slash commands, regardless of the configured text prefixes, so those
are never stored here. A guild with no stored prefixes uses DEFAULT_PREFIXES.
"""

import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

# The classic text prefixes. Used for DMs, and seeded onto the guilds the bot is
# already in the first time it runs (see PrefixStore.backfill). A guild that has
# never been configured otherwise gets *no* text prefixes (mention/slash only),
# so newly-joined servers start clean.
DEFAULT_PREFIXES = ("?", "/")

# Cap on how many prefixes a guild may set, to keep things sane.
MAX_PREFIXES = 10


def parse_prefixes(text):
    """Parse user input into an ordered, de-duplicated list of single-char prefixes.

    Whitespace is ignored, so '?/!' and '? / !' both give ['?', '/', '!']. The
    result is capped at MAX_PREFIXES. An empty/whitespace-only input gives [].
    """
    prefixes = []
    for char in text:
        if char.isspace():
            continue
        if char not in prefixes:
            prefixes.append(char)
    return prefixes[:MAX_PREFIXES]


def format_prefixes(prefixes):
    """Render a prefix list for display as space-separated inline code."""
    return " ".join(f"`{p}`" for p in prefixes)


class PrefixStore:
    """In-memory per-guild prefix cache backed by a sqlite database.

    Call :meth:`load` once at startup to open the database and populate the
    cache; :meth:`set` writes through to the database as changes happen. Reads
    (:meth:`get`) are served entirely from the cache, so they're cheap enough to
    run for every incoming message.
    """

    def __init__(self, path):
        self._path = path
        self._cache = {}
        self._conn = None
        # True when load() created the database (no file existed) -- the signal
        # for a one-time backfill of the guilds the bot is already in.
        self.created = False

    def load(self):
        """Open the database (creating the table if needed) and cache all rows."""
        # Check before connect(), which would create the file.
        self.created = self._path == ":memory:" or not os.path.exists(self._path)
        self._conn = sqlite3.connect(self._path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS guild_prefixes "
            "(guild_id INTEGER PRIMARY KEY, prefixes TEXT NOT NULL)"
        )
        self._conn.commit()
        self._cache = {}
        for guild_id, prefixes in self._conn.execute(
            "SELECT guild_id, prefixes FROM guild_prefixes"
        ):
            # A stored empty string means "configured with no text prefixes"; keep
            # the row so it stays distinct from a guild that was never configured.
            self._cache[guild_id] = parse_prefixes(prefixes)
        logger.info("Loaded prefixes for %d guild(s)", len(self._cache))
        return self

    def get(self, guild_id):
        """Return a copy of the prefix list to use for a message's prefixes.

        DMs (``guild_id is None``) use DEFAULT_PREFIXES. A configured guild uses
        its stored list, which may be empty (only @-mention and slash commands).
        An unconfigured guild also gets an empty list, so a server the bot joins
        starts out mention/slash only.
        """
        if guild_id is None:
            return list(DEFAULT_PREFIXES)
        return list(self._cache.get(guild_id, []))

    def set(self, guild_id, prefixes):
        """Cache and persist the prefix list for a guild; return the stored list."""
        prefixes = list(prefixes)
        self._cache[guild_id] = prefixes
        if self._conn is not None:
            self._conn.execute(
                "INSERT OR REPLACE INTO guild_prefixes (guild_id, prefixes) "
                "VALUES (?, ?)",
                (guild_id, "".join(prefixes)),
            )
            self._conn.commit()
        return prefixes

    def backfill(self, guild_ids):
        """Seed DEFAULT_PREFIXES for any of ``guild_ids`` not already configured.

        Run once on first startup (a freshly-created database) so the guilds the
        bot is already in keep the classic ``?``/``/`` prefixes, while guilds it
        joins afterwards start with none. Returns how many guilds were seeded.
        """
        count = 0
        for guild_id in guild_ids:
            if guild_id not in self._cache:
                self.set(guild_id, DEFAULT_PREFIXES)
                count += 1
        return count
