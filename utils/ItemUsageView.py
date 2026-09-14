"""
Views for the unified item-usage search (";<item name>"), covering
every source an item can come from: Raids, Story, Trials, and Units
(evolution materials).

If only one source has matches, that source's *Match view is sent
directly (e.g. RaidDropMatchView from utils/RaidsView.py) -- and if
that source itself only has one entry, resolve_source_result() skips
straight to that entry's own detail embed. If multiple sources match,
ItemUsagePickerView shows ONE combined dropdown listing every entry
across every source at once (not a button per source) -- picking any
option jumps straight to that entry's detail.
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


def resolve_source_result(
    source_key: str,
    item_name: str,
    raw_matches: list,
    back_embed: discord.Embed | None = None,
    back_view: discord.ui.View | None = None,
) -> tuple[discord.Embed, discord.ui.View, list]:
    """
    Given one source's raw matches, returns (embed, view, image_paths):
    - Exactly 1 match -> skip the intermediate list entirely and go
      straight to that single entry's own detail embed (a raid's page,
      a story chapter's page, etc.), with just a Back button if a back
      target was given.
    - 2+ matches -> the source's *MatchView (dropdown list), same as
      before.

    Shared by cogs/ItemSearch.py (top-level item search) and
    utils/UnitChoiceView.py ("Obtainable From"), so both behave the
    same way instead of each re-implementing this branching.
    """
    if source_key == "Raids":
        if len(raw_matches) == 1:
            raid = Models.Raid.from_raw(raw_matches[0])
            embed = EmbedBuilder.build_raid_detail_embed("World 2", raid)
            view = discord.ui.View(timeout=180)
            if back_embed is not None and back_view is not None:
                view.add_item(BackButton(back_embed, back_view))
            return embed, view, [raid.image]
        from utils.RaidsView import RaidDropMatchView
        raids = [Models.Raid.from_raw(r) for r in raw_matches]
        view = RaidDropMatchView("World 2", item_name, raids, back_embed=back_embed, back_view=back_view)
        return view.embed, view, []

    if source_key == "Story":
        if len(raw_matches) == 1:
            chapter_raw = raw_matches[0]
            chapter = Models.StoryChapter.from_raw(chapter_raw)
            world_label = chapter_raw.get("world_label", "")
            embed = EmbedBuilder.build_story_chapter_embed(world_label, chapter)
            view = discord.ui.View(timeout=180)
            if back_embed is not None and back_view is not None:
                view.add_item(BackButton(back_embed, back_view))
            return embed, view, [chapter.image]
        view = StoryDropMatchView(item_name, raw_matches, back_embed=back_embed, back_view=back_view)
        return view.embed, view, []

    if source_key == "Trials":
        if len(raw_matches) == 1:
            stage = Models.TrialStage.from_raw(raw_matches[0])
            embed = EmbedBuilder.build_trial_stage_embed("World 1", stage)
            view = discord.ui.View(timeout=180)
            if back_embed is not None and back_view is not None:
                view.add_item(BackButton(back_embed, back_view))
            return embed, view, [stage.image]
        view = TrialDropMatchView(item_name, raw_matches, back_embed=back_embed, back_view=back_view)
        return view.embed, view, []

    if source_key == "Units":
        if len(raw_matches) == 1:
            unit_id = raw_matches[0]["unit_id"]
            raw = DataLoader.get_unit(unit_id)
            unit = Models.Unit.from_raw(raw)
            view = UnitView(unit, initial_tab="evolution", back_embed=back_embed, back_view=back_view)
            embed = view.initial_embed()
            return embed, view, view.initial_image_paths()
        view = UnitMaterialMatchView(item_name, raw_matches, back_embed=back_embed, back_view=back_view)
        return view.embed, view, []

    if source_key == "Material Info":
        # A material name is unique (materials.json keys are unique),
        # so there's only ever exactly one match here -- always the
        # direct-detail path, no list variant needed.
        material_raw = raw_matches[0]
        material = Models.Material.from_raw(material_raw["id"], material_raw)
        embed = EmbedBuilder.build_material_detail_embed(material)
        view = discord.ui.View(timeout=180)
        if back_embed is not None and back_view is not None:
            view.add_item(BackButton(back_embed, back_view))
        return embed, view, [material.image]

    raise ValueError(f"Unknown source key: {source_key}")


class CombinedMatchSelect(discord.ui.Select):
    """One dropdown listing every individual match across every
    source, e.g. 'Fire Temple (Raids)', 'Starter Plains (Story)',
    'Unit A (Units)' -- picking any option jumps straight to that
    entry's own detail embed (via resolve_source_result with a
    single-item list, which always takes the direct-detail path)."""

    def __init__(self, item_name: str, raw_matches: dict[str, list], parent_view: "ItemUsagePickerView"):
        self.item_name = item_name
        self.parent_view = parent_view
        # (source_key, raw_entry) for every match, flattened across
        # every source -- index into this list is the option's value.
        self.entries: list[tuple[str, dict]] = []

        options = []
        for source_key, matches in raw_matches.items():
            for entry in matches:
                label = entry.get("name", "Unknown")
                options.append(discord.SelectOption(label=f"{label} ({source_key})", value=str(len(self.entries))))
                self.entries.append((source_key, entry))

        super().__init__(placeholder="Select where to view...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        source_key, raw_entry = self.entries[int(self.values[0])]
        embed, view, image_paths = resolve_source_result(
            source_key, self.item_name, [raw_entry],
            back_embed=self.parent_view.embed, back_view=self.parent_view,
        )
        files = EmbedBuilder.image_files_for(*image_paths)
        await interaction.response.edit_message(embed=embed, view=view, attachments=files)


class ItemUsagePickerView(discord.ui.View):
    """
    raw_matches: dict of source name -> raw match list, e.g.
    {"Raids": [...], "Units": [...]} -- only sources with at least
    one match should be included (callers filter this before
    constructing the view).

    Optionally takes a back_embed/back_view (e.g. the unit "Obtainable
    From" chooser) if this picker was reached from somewhere other
    than the top-level ItemSearch trigger.
    """

    def __init__(
        self,
        item_name: str,
        raw_matches: dict[str, list],
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.item_name = item_name
        self.raw_matches = raw_matches

        counts = {source: len(matches) for source, matches in raw_matches.items()}
        self.embed = EmbedBuilder.build_item_usage_picker_embed(item_name, counts)

        self.add_item(CombinedMatchSelect(item_name, raw_matches, self))

        if back_embed is not None and back_view is not None:
            self.add_item(BackButton(back_embed, back_view))