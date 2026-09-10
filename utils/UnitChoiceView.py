"""
Shown when a unit is looked up directly by its own name (not via
ability/passive trigger, which jump straight to a specific tab). Two
buttons: view the unit itself, or view where it's obtainable from
(reverse lookup across Raids/Story/Trials, matched by drop name).
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import BackButton, UnitView


class ViewUnitButton(discord.ui.Button):
    def __init__(self, parent_view: "UnitChoiceView"):
        super().__init__(label="View Unit", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        unit = self.parent_view.unit
        view = UnitView(unit, back_embed=self.parent_view.embed, back_view=self.parent_view)
        embed = view.initial_embed()
        files = EmbedBuilder.image_files_for(*view.initial_image_paths())
        await interaction.response.edit_message(embed=embed, view=view, attachments=files)


class ViewObtainableButton(discord.ui.Button):
    def __init__(self, parent_view: "UnitChoiceView"):
        super().__init__(label="Obtainable From", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Local imports to avoid a circular import at module load time
        # (RaidsView/ItemUsageView also import from UnitView).
        from utils.RaidsView import RaidDropMatchView
        from utils.ItemUsageView import StoryDropMatchView, TrialDropMatchView, ItemUsagePickerView

        unit = self.parent_view.unit

        raw_matches: dict[str, list] = {}
        raw_raids = DataLoader.find_raids_by_drop("world2", unit.name)
        if raw_raids:
            raw_matches["Raids"] = raw_raids
        raw_story = DataLoader.find_story_stages_by_drop(unit.name)
        if raw_story:
            raw_matches["Story"] = raw_story
        raw_trials = DataLoader.find_trial_stages_by_drop(unit.name)
        if raw_trials:
            raw_matches["Trials"] = raw_trials

        back_embed, back_view = self.parent_view.embed, self.parent_view

        if not raw_matches:
            embed = EmbedBuilder.build_unit_obtainable_embed(unit.name, [], [], [])
            fallback_view = discord.ui.View(timeout=180)
            fallback_view.add_item(BackButton(back_embed, back_view))
            await interaction.response.edit_message(embed=embed, view=fallback_view, attachments=[])
            return

        if len(raw_matches) == 1:
            source_key = next(iter(raw_matches))
            if source_key == "Raids":
                raids = [Models.Raid.from_raw(r) for r in raw_matches["Raids"]]
                view = RaidDropMatchView("World 2", unit.name, raids, back_embed=back_embed, back_view=back_view)
            elif source_key == "Story":
                view = StoryDropMatchView(unit.name, raw_matches["Story"], back_embed=back_embed, back_view=back_view)
            else:  # Trials
                view = TrialDropMatchView(unit.name, raw_matches["Trials"], back_embed=back_embed, back_view=back_view)
        else:
            view = ItemUsagePickerView(unit.name, raw_matches, back_embed=back_embed, back_view=back_view)

        await interaction.response.edit_message(embed=view.embed, view=view, attachments=[])


class UnitChoiceView(discord.ui.View):
    def __init__(self, unit: Models.Unit, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.unit = unit
        self.embed = EmbedBuilder.build_unit_choice_embed(unit.name)
        self.add_item(ViewUnitButton(self))
        self.add_item(ViewObtainableButton(self))