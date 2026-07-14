import asyncio
import stoat
from base import EconomyBot, Auth

bot = EconomyBot(command_prefix=Auth.COMMAND_PREFIX)


@bot.listen()
async def on_ready(event: stoat.ReadyEvent):
    # ReadyEvent can fire again on reconnect — only run the startup work once.
    # capture the authoritative server list from the ReadyEvent payload
    bot._ready_servers = list(getattr(event, "servers", []) or [])
    if bot._ready_once:
        return
    bot._ready_once = True
    servers = bot._ready_servers or list(getattr(bot, "servers", []) or [])
    print(f"✅ CartelBot (Stoat) online as {bot.me}")
    print(f"   Prefix: {Auth.COMMAND_PREFIX}   •   Servers: {len(servers)}")

    # Rotate through a list of status texts (also sets presence online).
    asyncio.create_task(bot.status_rotate_task())
    asyncio.create_task(bot.console_stats_task())
    asyncio.create_task(bot.server_breakdown_task())


if __name__ == "__main__":
    print("Starting CartelBot (Stoat)...")
    bot.run(Auth.TOKEN)
