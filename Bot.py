"""
Entry point. Run with: python bot.py

This file should stay thin — its only jobs are: start the bot, load
cogs, and sync slash commands. Actual command logic lives in cogs/,
not here.
"""

import asyncio
import logging
import os

import discord
from discord.ext import commands

import Config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("tdsinfobot")

# Cogs to load on startup. Add new cog module names here as they're built.
# Prefix-command cogs (units, gamemodes, mechanics, misc) need no syncing
INITIAL_COGS = [
    "cogs.Units",
    "cogs.Dev",
    "cogs.Gamemodes",
    "cogs.Mechanics",
    # "cogs.misc",
]


def _channel_role_check(ctx: commands.Context) -> bool:
    """
    Global command check applied to every prefix command: only usable
    in the questions/commands channels, and in the questions channel
    specifically, only by users with the configured role.

    Commands in cogs/Dev.py are exempt -- they're already gated
    separately (bot owner / DEV_USER_IDS) and should work from
    anywhere for whoever's authorized to run them.
    """
    if ctx.cog is not None and ctx.cog.qualified_name == "Dev":
        return True

    questions_channel_id = int(os.getenv("QUESTIONS_CHANNEL_ID"))
    commands_channel_id = int(os.getenv("COMMANDS_CHANNEL_ID"))

    if ctx.channel.id not in (questions_channel_id, commands_channel_id):
        return False

    if ctx.channel.id == questions_channel_id:
        valid_role_id = int(os.getenv("VALID_ROLES"))
        if not any(role.id == valid_role_id for role in ctx.author.roles):
            return False

    return True


class TDSInfoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        # Privileged intents — these must ALSO be enabled manually in the
        # Discord Developer Portal (Bot page > Privileged Gateway Intents)
        # or the bot will fail to start with PrivilegedIntentsRequired.
        intents.message_content = True  # needed for prefix commands (!unit, etc.)
        intents.members = True          # needed for member join events, member lookups

        super().__init__(command_prefix=Config.COMMAND_PREFIX, intents=intents)
        self.add_check(_channel_role_check)

    async def setup_hook(self) -> None:
        for cog in INITIAL_COGS:
            try:
                await self.load_extension(cog)
                log.info("Loaded cog: %s", cog)
            except Exception:
                log.exception("Failed to load cog: %s", cog)

        # Sync slash commands. If GUILD_ID is set, sync instantly to that
        # test server (good for development). Otherwise sync globally,
        # which can take up to an hour to propagate.
        if Config.GUILD_ID:
            guild = discord.Object(id=int(Config.GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d command(s) to guild %s", len(synced), Config.GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d command(s) globally", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        # A failed global check (wrong channel / missing role) should
        # fail silently, matching the ";" trigger's behavior elsewhere
        if isinstance(error, commands.CheckFailure):
            return
        if isinstance(error, commands.CommandNotFound):
            return
        log.exception("Unhandled command error in %s", ctx.command, exc_info=error)


async def main():
    Config.validate()
    bot = TDSInfoBot()
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())