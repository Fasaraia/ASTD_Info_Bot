"""
View attached to an orb's detail embed. If the orb is unit-specific
(orb.unit_specific has one or more unit ids), a dropdown lets you jump
straight to any of those units' pages -- with a Back button on the
resulting UnitView pointing back to the orb.
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import UnitView


class OrbUnitSelect(discord.ui.Select):
    def __init__(self, unit_ids: list[str], parent_view: "OrbView"):
        self.unit_ids = unit_ids
        self.parent_view = parent_view

        options = []
        for i, unit_id in enumerate(unit_ids):
            raw = DataLoader.get_unit(unit_id)
            unit_name = raw["base"]["name"] if raw else unit_id
            options.append(discord.SelectOption(label=unit_name, value=str(i)))

        super().__init__(placeholder="View a specific unit...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        unit_id = self.unit_ids[int(self.values[0])]
        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            await interaction.response.edit_message(content="That unit's data could not be found.", embed=None, view=None)
            return

        unit = Models.Unit.from_raw(raw)
        view = UnitView(unit, back_embed=self.parent_view.embed, back_view=self.parent_view)
        embed = view.initial_embed()
        files = EmbedBuilder.image_files_for(*view.initial_image_paths())
        await interaction.response.edit_message(embed=embed, view=view, attachments=files)


class OrbView(discord.ui.View):
    def __init__(
        self,
        orb: Models.Orb,
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.orb = orb
        self.embed = EmbedBuilder.build_orb_detail_embed(orb)
        if orb.unit_specific:
            self.add_item(OrbUnitSelect(orb.unit_specific, self))
        if back_embed is not None and back_view is not None:
            from utils.UnitView import BackButton
            self.add_item(BackButton(back_embed, back_view))