[![pre-commit](https://github.com/freiheit/MvKDiceBot/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/pre-commit.yml)
[![Python Checks](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml)
[![Tests](https://github.com/freiheit/MvKDiceBot/actions/workflows/test.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/test.yml)
[![CodeQL](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates)

# MvKDiceBot

Dice bot for MvK ruleset...

## Commands

The bot understands these commands. Each can be invoked three ways: with a
text prefix (`?mvkroll 1d20 2d10`, plus aliases like `?r`, `?roll`, `?p`), by
mentioning the bot (`@MvkDiceBot roll 1d20 2d10`), or as a slash command
(`/mvkroll dice:1d20 2d10`).

Each server has its own text prefixes. Servers the bot was already in keep the
classic `?` and `/` (so `?r 1d20` and `/r 1d20` both work); a server the bot
joins fresh starts with no text prefixes (only @-mention and slash commands). A
member with the **Manage Server** permission changes them with `/setprefixes` —
e.g. `/setprefixes ?/!`, or `/setprefixes none` for only @-mention and slash
commands; run it with no argument to see the current set. The bot always responds
to @-mentions and to its slash commands regardless.

- `mvkroll` — rolls a dice pool and applies the MvK rules math (action total,
  impact, advantage/disadvantage, fumbles, and critical success). It also
  understands several keywords: `overwhelmed`/`staggered` (stress — reduces your
  largest die one size before rolling, or scratches it if both apply); `vs N`
  (or `counter N`) to compare your action total against a counter; `+N`/`-N` to
  adjust the action total and `impact +N` to adjust impact; `boost dN`/`reduce
  dN` to step a die up/down a size before rolling; `burnout` to total your
  highest three dice; and the named effects `unstable` (−1 action total) and
  `burst` (+2 impact, rolled with disadvantage). Also available as the slash
  command `/r` (Discord has
  no slash-command aliases, so `/r` is a second command that does the same
  thing).
- `plainroll` — just rolls dice and adds up `+N`/`-N` modifiers. For a single
  d20 it also calls out 13th Age-flavored results (crit, fumble, even/odd,
  possible two-weapon hit) and, when this channel's escalation die is set, shows
  it and an escalation-adjusted total. Also available as the slash command `/p`.
- `anyroll` — like `plainroll` but with no die-size restriction, so `d100`,
  `3d3`, `d7`, `d2`, etc. all work. Rolls the pool, applies `+N`/`-N` modifiers,
  and gives a total — no MvK/13th Age rules or crit/even/odd callouts. Aliases
  `a`, `rollany`; also the slash command `/a`.
- `escalation` — tracks the 13th Age escalation die (0–6) for the current
  channel. `?escalation`/`/escalation` (text aliases `?esc`/`?e`, plus the `/esc`
  slash command) shows it; `+1`/`next` advances a round, `-1`/`back` steps down,
  `reset` starts a new battle, and a number `0`–`6` sets it. A channel's value
  resets to 0 after 12 hours of inactivity.
- `nextround` — shorthand for advancing the escalation die a round (same as
  `escalation next`). Available as `?nextround`/`/nextround` (text aliases
  `?next`/`?n`, plus the `/n` slash command).
- `help` — auto-generated command list and usage. Available as `?help`,
  `@MvkDiceBot help`, or `/help` (optionally pass a command name, e.g.
  `/help command:mvkroll`).
- `setprefixes` — shows or sets this server's text command prefixes (pass `none`
  to use only @-mention and slash commands). Available as `?setprefixes`,
  `@MvkDiceBot setprefixes`, or `/setprefixes`, restricted to the server owner,
  administrators, or members with Manage Server (and only shown in `?help` to
  them).

Editing a text/mention roll message updates the bot's existing reply and
re-rolls only the dice you added (existing dice are kept). Each prior `Dice:`
line is shown above the new result, struck through as small text, so others can
see what changed. Slash commands can't be edited, so this applies to the
`?`/mention forms only.

Slash commands are registered with Discord automatically on startup. If you set
`primary_guilds` (a list of guild/server IDs) in `mvkdicebot.ini`, they are
synced to those servers instantly. Otherwise they are synced globally, which can
take up to ~1 hour to appear in Discord's `/` menu the first time after a new
deploy. The text and mention forms always work immediately.

## Invite My instance

<https://discord.com/api/oauth2/authorize?client_id=1168083075515826186&permissions=274877910016&scope=bot%20applications.commands>

## Installing

### Example on CentOS Stream9

1. Install python: `yum install python3.11 python3.11-devel python3.11-pip python3.11-pip-wheel python3.11-wheel`
2. Make a venv: `python3.11 -m venv --symlinks --system-site-packages .venv`
3. Install requirements into venv: `./.venv/bin/pip install -r requirements.txt`
4. Create a bot account: <https://discord.com/developers/applications/>
5. On the application's "OAuth2" page, generate an invite URL:
   - Scopes: bot, applications.commands
   - Bot Permissions: Read Messages/View Channels, Send Messages, Send Messages in Threads
   - Copy and save the generated url at the end of the page.
6. On the application's "Bot" configuration page, turn on "Message Content Intent".
7. Still on the "Bot" page, click the "Reset Token" button and copy the new token value.
   - This is the app's authorization token. Never check it in to source control.
8. Copy `mvkdicebot.example.ini` to `mvkdicebot.ini`
9. Edit the  `mvkdicebot.ini` file
   - add the authorization token
   - add the OAuth2 URL in a comment, in case you need it later.
10. Use the OAuth2 URL to authorize the bot to talk to your server.

You should be able to run the bot with `./run.sh`

You can test the dice parsing and rolling code with `python test.py`
