[![pre-commit](https://github.com/freiheit/MvKDiceBot/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/pre-commit.yml)
[![Python Checks](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml)
[![Tests](https://github.com/freiheit/MvKDiceBot/actions/workflows/test.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/test.yml)
[![CodeQL](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates)

# MvKDiceBot

Dice bot for MvK ruleset...

## Commands

The bot understands these commands. Each can be invoked three ways: with the
text prefix (`?mvkroll 1d20 2d10`, plus aliases like `?r`, `?roll`, `?p`), by
mentioning the bot (`@MvkDiceBot roll 1d20 2d10`), or as a slash command
(`/mvkroll dice:1d20 2d10`).

- `mvkroll` — rolls a dice pool and applies the MvK rules math (action total,
  impact, advantage/disadvantage, fumbles). Also available as the slash command
  `/r` (Discord has no slash-command aliases, so `/r` is a second command that
  does the same thing).
- `plainroll` — just rolls dice and adds up `+N`/`-N` modifiers. For a single
  d20 it also calls out 13th Age-flavored results (crit, fumble, even/odd,
  possible two-weapon hit) and, when this channel's escalation die is set, shows
  it and an escalation-adjusted total. Also available as the slash command `/p`.
- `escalation` — tracks the 13th Age escalation die (0–6) for the current
  channel. `?escalation`/`/escalation` (text aliases `?esc`/`?e`, plus the `/esc`
  slash command) shows it; `+1`/`next` advances a round, `-1`/`back` steps down,
  `reset` starts a new battle, and a number `0`–`6` sets it. A channel's value
  resets to 0 after 12 hours of inactivity.
- `help` — auto-generated command list and usage. Available as `?help`,
  `@MvkDiceBot help`, or `/help` (optionally pass a command name, e.g.
  `/help command:mvkroll`).

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
