"""
Views for the unified item-usage search (";<item name>"), covering
every source an item can come from: Raids, Story, Trials, and Units
(evolution materials).

If only one source has matches, that source's *Match view is sent
directly (e.g. RaidDropMatchView from utils/RaidsView.py). If multiple
sources match, ItemUsagePickerView is sent first -- its buttons open
each source's match view, each with a Back button pointing back here.
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import BackButton, UnitView


class StoryDropSelect(discord.ui.Select):
    def __init__(self, chapters: list[Models.StoryChapter], parent_view: "StoryDropMatchView"):
        options = [
            discord.SelectOption(label=ch.name, value=str(i))
            for i, ch in enumerate(chapters)
        ]
        super().__init__(placeholder="View a specific stage...", options=options[:25])
        self.chapters = chapters
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        chapter = self.chapters[int(self.values[0])]
        embed = EmbedBuilder.build_story_chapter_embed(self.parent_view.world_labels[int(self.values[0])], chapter)
        image_file = EmbedBuilder.image_file_for(chapter.image)
        attachments = [image_file] if image_file else []

        detail_view = discord.ui.View(timeout=180)
        detail_view.add_item(BackButton(self.parent_view.embed, self.parent_view))
        await interaction.response.edit_message(embed=embed, view=detail_view, attachments=attachments)


class StoryDropMatchView(discord.ui.View):
    def __init__(
        self,
        item_name: str,
        raw_chapters: list[dict],
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.chapters = [Models.StoryChapter.from_raw(c) for c in raw_chapters]
        # Kept alongside self.chapters (same order/index) so the select
        # callback can look up which world each result came from.
        self.world_labels = [c.get("world_label", "") for c in raw_chapters]
        self.embed = EmbedBuilder.build_story_drop_matches_embed(item_name, self.chapters)
        if self.chapters:
            self.add_item(StoryDropSelect(self.chapters, self))
        if back_embed is not None and back_view is not None:
            self.add_item(BackButton(back_embed, back_view))


class TrialDropSelect(discord.ui.Select):
    def __init__(self, stages: list[Models.TrialStage], parent_view: "TrialDropMatchView"):
        options = [
            discord.SelectOption(label=s.name, value=str(i))
            for i, s in enumerate(stages)
        ]
        super().__init__(placeholder="View a specific trial...", options=options[:25])
        self.stages = stages
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        stage = self.stages[int(self.values[0])]
        embed = EmbedBuilder.build_trial_stage_embed("World 1", stage)
        image_file = EmbedBuilder.image_file_for(stage.image)
        attachments = [image_file] if image_file else []

        detail_view = discord.ui.View(timeout=180)
        detail_view.add_item(BackButton(self.parent_view.embed, self.parent_view))
        await interaction.response.edit_message(embed=embed, view=detail_view, attachments=attachments)


class TrialDropMatchView(discord.ui.View):
    def __init__(
        self,
        item_name: str,
        raw_stages: list[dict],
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.stages = [Models.TrialStage.from_raw(s) for s in raw_stages]
        self.embed = EmbedBuilder.build_trial_drop_matches_embed(item_name, self.stages)
        if self.stages:
            self.add_item(TrialDropSelect(self.stages, self))
        if back_embed is not None and back_view is not None:
            self.add_item(BackButton(back_embed, back_view))


class UnitMaterialSelect(discord.ui.Select):
    def __init__(self, units: list[dict], parent_view: "UnitMaterialMatchView"):
        options = [
            discord.SelectOption(label=u["name"], value=str(i))
            for i, u in enumerate(units)
        ]
        super().__init__(placeholder="View a specific unit...", options=options[:25])
        self.units = units
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        unit_id = self.units[int(self.values[0])]["unit_id"]
        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            await interaction.response.edit_message(content="That unit's data could not be found.", embed=None, view=None)
            return

        unit = Models.Unit.from_raw(raw)
        # Opens straight to the Evolution tab, since that's where the
        # material actually matters -- with Back pointing at this
        # match list.
        view = UnitView(unit, initial_tab="evolution", back_embed=self.parent_view.embed, back_view=self.parent_view)
        embed = view.initial_embed()
        files = EmbedBuilder.image_files_for(*view.initial_image_paths())
        await interaction.response.edit_message(embed=embed, view=view, attachments=files)


class UnitMaterialMatchView(discord.ui.View):
    def __init__(
        self,
        item_name: str,
        units: list[dict],
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.embed = EmbedBuilder.build_unit_material_matches_embed(item_name, units)
        if units:
            self.add_item(UnitMaterialSelect(units, self))
        if back_embed is not None and back_view is not None:
            self.add_item(BackButton(back_embed, back_view))


class SourceButton(discord.ui.Button):
    def __init__(self, label: str, source_key: str, parent_view: "ItemUsagePickerView"):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.source_key = source_key
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        item_name = self.parent_view.item_name

        if self.source_key == "Raids":
            from utils.RaidsView import RaidDropMatchView
            raids = [Models.Raid.from_raw(r) for r in self.parent_view.raw_matches["Raids"]]
            view = RaidDropMatchView("World 2", item_name, raids, back_embed=self.parent_view.embed, back_view=self.parent_view)
        elif self.source_key == "Story":
            view = StoryDropMatchView(item_name, self.parent_view.raw_matches["Story"], back_embed=self.parent_view.embed, back_view=self.parent_view)
        elif self.source_key == "Trials":
            view = TrialDropMatchView(item_name, self.parent_view.raw_matches["Trials"], back_embed=self.parent_view.embed, back_view=self.parent_view)
        elif self.source_key == "Units":
            view = UnitMaterialMatchView(item_name, self.parent_view.raw_matches["Units"], back_embed=self.parent_view.embed, back_view=self.parent_view)
        else:
            return

        await interaction.response.edit_message(embed=view.embed, view=view, attachments=[])


class ItemUsagePickerView(discord.ui.View):
    """
    raw_matches: dict of source name -> raw match list, e.g.
    {"Raids": [...], "Units": [...]} -- only sources with at least
    one match should be included (callers filter this before
    constructing the view).
    """

    def __init__(self, item_name: str, raw_matches: dict[str, list], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.item_name = item_name
        self.raw_matches = raw_matches

        counts = {source: len(matches) for source, matches in raw_matches.items()}
        self.embed = EmbedBuilder.build_item_usage_picker_embed(item_name, counts)

        for source in raw_matches:
            self.add_item(SourceButton(source, source, self))