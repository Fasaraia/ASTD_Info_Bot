"""
Shown when an ability/passive name matches more than one unit (e.g.
several units share a passive called "Heat Aura"). Presents a dropdown
of "<Unit Name> (<context>)" options; picking one opens that unit's
UnitView on the matching tab/entry, same as a direct unique match
would have.
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import UnitView


class DisambiguationSelect(discord.ui.Select):
    def __init__(self, matches: list[tuple[str, int]], tab_key: str):
        # matches: list of (unit_id, index) -- the ability/passive index
        # within that unit's list.
        self.matches = matches
        self.tab_key = tab_key

        options = []
        for i, (unit_id, index) in enumerate(matches):
            raw = DataLoader.get_unit(unit_id)
            unit_name = raw["base"]["name"] if raw else unit_id
            options.append(discord.SelectOption(label=unit_name, value=str(i)))

        super().__init__(placeholder="Multiple units match -- pick one...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        unit_id, index = self.matches[int(self.values[0])]
        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            await interaction.response.edit_message(
                content="That unit's data could not be found.", embed=None, view=None
            )
            return

        unit = Models.Unit.from_raw(raw)
        view = UnitView(unit, initial_tab=self.tab_key, initial_index=index)
        embed = view.initial_embed()
        files = EmbedBuilder.image_files_for(*view.initial_image_paths())

        await interaction.response.edit_message(content=None, embed=embed, view=view, attachments=files)


class DisambiguationView(discord.ui.View):
    def __init__(self, matches: list[tuple[str, int]], tab_key: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(DisambiguationSelect(matches, tab_key))


def build_disambiguation_embed(name: str, count: int) -> discord.Embed:
    return discord.Embed(
        description=f"**{count}** units have an ability/passive named **{name}**. Pick one below:",
    )