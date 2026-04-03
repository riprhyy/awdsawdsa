import os
import json
import asyncio
from urllib.parse import parse_qs
from your_bot_module import bot  

async def update_lastfm_user(discord_user_id: int, token: str):
    """Fetch username from Last.fm and update database."""
    try:
        username = await bot.lastfmhandler.get_username_from_token(token)
        if username:
            await bot.db.execute(
                """
                INSERT INTO lastfm_users (discord_user_id, lastfm_username)
                VALUES ($1, $2)
                ON CONFLICT (discord_user_id) DO UPDATE
                SET lastfm_username = EXCLUDED.lastfm_username;
                """,
                discord_user_id,
                username
            )
    except Exception as e:
        print(f"Error updating Last.fm user: {e}")

def handler(request, response):
    """
    Vercel serverless function entry point.
    Expects query parameters:
      - token
      - discord_user_id
    """
    
    query = parse_qs(request.query_string.decode())
    token = query.get("token", [None])[0]
    discord_user_id = query.get("discord_user_id", [None])[0]

    if not token or not discord_user_id:
        response.status_code = 400
        response.write("Missing token or discord_user_id")
        return

    try:
        discord_user_id = int(discord_user_id)
    except ValueError:
        response.status_code = 400
        response.write("Invalid discord_user_id")
        return

    asyncio.run(update_lastfm_user(discord_user_id, token))

    response.write("Last.fm account linked successfully! You can close this page.")
