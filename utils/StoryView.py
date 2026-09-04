"""
View attached to a story overview message: a dropdown listing every
chapter by name. Selecting one swaps the embed to that chapter's
detail view.
"""

import discord

from core import EmbedBuilder, Models


class ChapterSelect(discord.ui.Select):
    def __init__(self, world_label: str, chapters: list[Models.StoryChapter]):
        # Discord caps a select at 25 options -- if a world ever has
        # more chapters than that, this will need paging across
        # multiple Select menus. Not an issue at current chapter counts.
        options = [
            discord.SelectOption(label=f"{ch.stage_number}. {ch.name}", value=str(i))
            for i, ch in enumerate(chapters)
        ]
        super().__init__(placeholder="View a specific stage...", options=options[:25])
        self.world_label = world_label
        self.chapters = chapters

    async def callback(self, interaction: discord.Interaction):
        chapter = self.chapters[int(self.values[0])]
        embed = EmbedBuilder.build_story_chapter_embed(self.world_label, chapter)
        image_file = EmbedBuilder.image_file_for(chapter.image)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(embed=embed, view=self, attachments=attachments)


class StoryView(discord.ui.View):
    def __init__(self, world_label: str, chapters: list[Models.StoryChapter], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(ChapterSelect(world_label, chapters))