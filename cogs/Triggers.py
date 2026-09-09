"""
The single shared ";<name>" message listener for the whole bot.

This cog owns ONLY: detecting a ";" trigger message, the channel/role
restriction, and routing the name through each domain cog in priority
order. It contains no domain-specific logic itself -- every check
below is a call into another cog's handle_x_trigger(channel, name)
method, which returns True if it matched (stop the chain) or False
(try the next one).

Order: unit -> ability -> passive -> status effect -> raid enchant ->
item usage search (raids/story/trials/unit materials, unified). Add
new domains by adding one more delegated check here.
"""

import logging
import os

import discord
from discord.ext import commands

log = logging.getLogger("tdsinfobot.triggers")


class Triggers(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _channel_role_allowed(self, message: discord.Message) -> bool:
        valid_channels = (int(os.getenv("QUESTIONS_CHANNEL_ID")), int(os.getenv("COMMANDS_CHANNEL_ID")))
        if message.channel.id not in valid_channels:
            return False

        if message.channel.id == int(os.getenv("QUESTIONS_CHANNEL_ID")):
            valid_role_id = int(os.getenv("VALID_ROLES"))
            if not any(role.id == valid_role_id for role in message.author.roles):
                return False

        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not self._channel_role_allowed(message):
            return

        content = message.content.strip()
        if not content.startswith(";"):
            return

        name = content[1:].strip()
        if not name:
            return

        channel = message.channel

        units_cog = self.bot.get_cog("Units")
        if units_cog is not None:
            if await units_cog.handle_unit_trigger(channel, name):
                return
            if await units_cog.handle_ability_trigger(channel, name):
                return
            if await units_cog.handle_passive_trigger(channel, name):
                return

        mechanics_cog = self.bot.get_cog("Mechanics")
        if mechanics_cog is not None:
            if await mechanics_cog.handle_status_effect_trigger(channel, name):
                return

        gamemodes_cog = self.bot.get_cog("Gamemodes")
        if gamemodes_cog is not None:
            if await gamemodes_cog.handle_raid_enchant_trigger(channel, name):
                return

        itemsearch_cog = self.bot.get_cog("ItemSearch")
        if itemsearch_cog is not None:
            if await itemsearch_cog.handle_item_usage_trigger(channel, name):
                return

        # No domain matched -- nothing to do.


async def setup(bot: commands.Bot):
    await bot.add_cog(Triggers(bot))