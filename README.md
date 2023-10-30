[![CodeQL](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql)
[![Pylint](https://github.com/freiheit/MvKDiceBot/actions/workflows/pylint.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/pylint.yml)

# MvKDiceBot
Dice bot for MvK ruleset...

## Invite My instance:
https://discord.com/api/oauth2/authorize?client_id=1168083075515826186&permissions=274877910016&scope=bot%20applications.commands

## Installing

### Example on CentOS Stream9:
1. Install python: yum install python3.11 python3.11-devel python3.11-pip python3.11-pip-wheel python3.11-wheel
2. Make a venv: python3.11 -m venv --symlinks --system-site-packages .venv
3. Install requirements into venv: ./.venv/bin/pip install -r requirements.txt
4. Copy mvkdicebot.example.ini to mvkdicebot.ini
5. Create a bot account and get a token: https://discord.com/developers/applications/
6. Put the token into mvkdicebot.ini
7. Generate an invite URL:
   - Scopes: bot, applications.commands
   - Bot Permissions: Read Messages/View Channels, Send Messages, Send Messages in Threads
