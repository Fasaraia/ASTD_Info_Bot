"""
View attached to a trials overview message: a dropdown listing every
trial stage by name. Selecting one swaps the embed to that stage's
detail view. Same pattern as StoryView, minus the act range concept.
"""

import discord

from core import EmbedBuilder, Models


class TrialStageSelect(discord.ui.Select):
    def __init__(self, world_label: str, stages: list[Models.TrialStage], parent_view: "TrialsView"):
        # Discord caps a select at 25 options -- if this ever grows
        # past that, it'll need paging across multiple Select menus.
        options = [
            discord.SelectOption(label=f"{s.stage_number}. {s.name}", value=str(i))
            for i, s in enumerate(stages)
        ]
        super().__init__(placeholder="View a specific trial...", options=options[:25])
        self.world_label = world_label
        self.stages = stages
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        stage = self.stages[int(self.values[0])]
        embed = EmbedBuilder.build_trial_stage_embed(self.world_label, stage)
        image_file = EmbedBuilder.image_file_for(stage.image)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(embed=embed, view=self.parent_view, attachments=attachments)


class TrialsView(discord.ui.View):
    def __init__(self, world_label: str, stages: list[Models.TrialStage], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(TrialStageSelect(world_label, stages, self))