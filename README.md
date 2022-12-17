# Tiny discord bot for personal use on my server

Asyncio and postgresql practice.
Initial idea was create user's own channel by just logging into special voice channel. 
Now these functionality stays in channels_manager.py module as one of others COGS.

## Project details

- creating own voice channel where are you administrator of room
- track users activities (if enabled in discord settings)
  - creating gameroles (special server roles associated with game activity)
  - better inform other users about created channel (rename created channel to current activity name and change channel category)
  - gathering user's activity time to providing spent time in game
- music module using lavalink player API
- restful API around discord db abstractions 
## Want to use this project?

Spin up the containers:

set enviroment variables into env file in root directory

```sh
$ docker-compose up -d --build
```