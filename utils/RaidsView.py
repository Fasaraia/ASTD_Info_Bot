"""
Views for raid lookups:
- RaidsView: attached to an enchant-filtered overview (";darkraids"
  etc). A dropdown lists every raid on that list; picking one opens
  its full detail embed with a Back button to return here.
- RaidDropMatchView: attached to item-drop search results
  (";<item name>"). Same idea -- dropdown of matching raids, Back
  button to return to the results.

Raids have no tabs (unlike units), so "detail" is a single embed with
just a Back button attached, not a full custom view.
"""

import discord

from core import EmbedBuilder, Models
from utils.UnitView import BackButton


class _RaidDetailView(discord.ui.View):
    """Minimal view for a single raid's detail embed: just a Back
    button pointing at whatever list it was opened from."""

    def __init__(self, back_embed: discord.Embed, back_view: discord.ui.View, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(BackButton(back_embed, back_view))


class RaidSelect(discord.ui.Select):
    def __init__(self, world_label: str, raids: list[Models.Raid], parent_view: "RaidsView"):
        options = [
            discord.SelectOption(label=raid.name, value=str(i))
            for i, raid in enumerate(raids)
        ]
        super().__init__(placeholder="View a specific raid...", options=options[:25])
        self.world_label = world_label
        self.raids = raids
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        raid = self.raids[int(self.values[0])]
        embed = EmbedBuilder.build_raid_detail_embed(self.world_label, raid)
        image_file = EmbedBuilder.image_file_for(raid.image)
        attachments = [image_file] if image_file else []

        detail_view = _RaidDetailView(back_embed=self.parent_view.embed, back_view=self.parent_view)
        await interaction.response.edit_message(embed=embed, view=detail_view, attachments=attachments)


class RaidsView(discord.ui.View):
    """Attached to an enchant-filtered raid overview."""

    def __init__(self, world_label: str, enchant_label: str, raids: list[Models.Raid], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.embed = EmbedBuilder.build_raids_overview_embed(world_label, enchant_label, raids)
        self.add_item(RaidSelect(world_label, raids, self))


class RaidDropSelect(discord.ui.Select):
    def __init__(self, world_label: str, raids: list[Models.Raid], parent_view: "RaidDropMatchView"):
        options = [
            discord.SelectOption(label=raid.name, value=str(i))
            for i, raid in enumerate(raids)
        ]
        super().__init__(placeholder="View a specific raid...", options=options[:25])
        self.world_label = world_label
        self.raids = raids
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        raid = self.raids[int(self.values[0])]
        embed = EmbedBuilder.build_raid_detail_embed(self.world_label, raid)
        image_file = EmbedBuilder.image_file_for(raid.image)
        attachments = [image_file] if image_file else []

        detail_view = _RaidDetailView(back_embed=self.parent_view.embed, back_view=self.parent_view)
        await interaction.response.edit_message(embed=embed, view=detail_view, attachments=attachments)


class RaidDropMatchView(discord.ui.View):
    """Attached to item-drop search results. Optionally takes a
    back_embed/back_view (e.g. the item usage picker) if this view was
    reached from a broader multi-source search rather than directly."""

    def __init__(
        self,
        world_label: str,
        item_name: str,
        raids: list[Models.Raid],
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.embed = EmbedBuilder.build_raid_drop_matches_embed(item_name, raids)
        if raids:
            self.add_item(RaidDropSelect(world_label, raids, self))
        if back_embed is not None and back_view is not None:
            self.add_item(BackButton(back_embed, back_view))