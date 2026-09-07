"""
Gamemode commands. Story mode: !w1story and !w2story show an overview
of every chapter (stage number, enchant, act range, drops), with a
dropdown to open a specific chapter's details.

Trials (World 1 only): !w1trials, same overview + dropdown pattern
but no act range.
"""

import logging

from discord.ext import commands

from core import DataLoader, EmbedBuilder, Models
from utils.StoryView import StoryView
from utils.TrialsView import TrialsView

log = logging.getLogger("tdsinfobot.gamemodes")


class Gamemodes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_story_chapters(self, world: str) -> list[Models.StoryChapter]:
        data = DataLoader.get_gamemode_file(world, "story")
        raw_chapters = data.get("chapters", [])
        return [Models.StoryChapter.from_raw(c) for c in raw_chapters]

    def _get_trial_stages(self, world: str) -> list[Models.TrialStage]:
        data = DataLoader.get_gamemode_file(world, "trials")
        raw_stages = data.get("stages", [])
        return [Models.TrialStage.from_raw(s) for s in raw_stages]

    async def _send_story_overview(self, ctx: commands.Context, world: str, world_label: str):
        chapters = self._get_story_chapters(world)
        embed = EmbedBuilder.build_story_overview_embed(world_label, chapters)
        view = StoryView(world_label, chapters)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="w1story", help="Show World 1 story stages.")
    async def w1story(self, ctx: commands.Context):
        await self._send_story_overview(ctx, "world1", "World 1")

    @commands.command(name="w2story", help="Show World 2 story stages.")
    async def w2story(self, ctx: commands.Context):
        await self._send_story_overview(ctx, "world2", "World 2")

    @commands.command(name="trials", help="Show World 1 trial stages.")
    async def trials(self, ctx: commands.Context):
        stages = self._get_trial_stages("world1")
        embed = EmbedBuilder.build_trials_overview_embed("World 1", stages)
        view = TrialsView("World 1", stages)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamemodes(bot))