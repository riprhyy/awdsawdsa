import os
import asyncio
import asyncpg
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

# Environment variables for DB
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

# Placeholder for your Last.fm API handler
class LastFMHandler:
    async def get_username_from_token(self, token: str):
        """
        Exchange Last.fm token for the username.
        Replace with your actual API request logic.
        """
        import aiohttp

        API_KEY = os.environ.get("LASTFM_API_KEY")
        async with aiohttp.ClientSession() as session:
            url = f"http://ws.audioscrobbler.com/2.0/?method=auth.getSession&api_key={API_KEY}&token={token}&format=json"
            async with session.get(url) as r:
                data = await r.json()
                return data.get("session", {}).get("name")  # username

lastfm_handler = LastFMHandler()

async def update_lastfm_user(discord_user_id: int, token: str):
    username = await lastfm_handler.get_username_from_token(token)
    if not username:
        print("Failed to get Last.fm username")
        return

    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )
    try:
        await conn.execute(
            """
            INSERT INTO lastfm_users (discord_user_id, lastfm_username)
            VALUES ($1, $2)
            ON CONFLICT (discord_user_id) DO UPDATE
            SET lastfm_username = EXCLUDED.lastfm_username;
            """,
            discord_user_id,
            username
        )
    finally:
        await conn.close()

# Vercel entry point
def handler(request, response):
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
