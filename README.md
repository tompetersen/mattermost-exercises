# Mattermost bot for recurring exercises

This bot for mattermost can use a specified channel to publish a random choice 
of exercises regularly. Users can take the challenge. Accomplished exercise sets
are recorded and you get exercise statistics for every user (in progress).

## Setup 

- Create `bot.conf` file similar to the example config for your mattermost installation (currently required in the bot dir)
- create channel and bot user in mattermost
- run the bot and profit ;)

## Commands

The bot can tell you available commands: `@bot-username help`

## TODO

- `current` command: Show current workout set again
- `next` command: Show time of next workout set
- statistics, statistics, statistics, ...
