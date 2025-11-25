[![Python Checks](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/python.yml)
[![CodeQL](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/github-code-scanning/codeql)
[![Dependabot Updates](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/freiheit/MvKDiceBot/actions/workflows/dependabot/dependabot-updates)

# MvKDiceBot
Dice bot for MvK ruleset...

## Invite My instance:
https://discord.com/api/oauth2/authorize?client_id=1168083075515826186&permissions=274877910016&scope=bot%20applications.commands

## Installing

### Example on CentOS Stream9:
1. Install python: `yum install python3.11 python3.11-devel python3.11-pip python3.11-pip-wheel python3.11-wheel`
2. Make a venv: `python3.11 -m venv --symlinks --system-site-packages .venv`
3. Install requirements into venv: `./.venv/bin/pip install -r requirements.txt`
4. Create a bot account: https://discord.com/developers/applications/
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
