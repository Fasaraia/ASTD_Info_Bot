"""
View attached to a status effect results message: Previous/Next
buttons to page through matches 25 at a time, plus a dropdown (one
per page) listing that page's units -- picking one opens that unit's
UnitView, same as any other unit lookup.
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import UnitView


class UnitPickSelect(discord.ui.Select):
    def __init__(self, page_matches: list[dict], parent_view: "StatusEffectView"):
        options = [
            discord.SelectOption(label=match["name"], value=str(i))
            for i, match in enumerate(page_matches)
        ]
        super().__init__(placeholder="View a unit...", options=options)
        self.page_matches = page_matches
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        unit_id = self.page_matches[int(self.values[0])]["unit_id"]
        raw = DataLoader.get_unit(unit_id)
        if raw is None:
            await interaction.response.edit_message(content="That unit's data could not be found.", embed=None, view=None)
            return

        unit = Models.Unit.from_raw(raw)
        view = UnitView(unit)
        embed = view.initial_embed()
        files = EmbedBuilder.image_files_for(*view.initial_image_paths())
        await interaction.response.edit_message(content=None, embed=embed, view=view, attachments=files)


class PrevPageButton(discord.ui.Button):
    def __init__(self, parent_view: "StatusEffectView"):
        super().__init__(label="◀ Previous", style=discord.ButtonStyle.secondary, disabled=(parent_view.page == 0))
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.go_to_page(interaction, self.parent_view.page - 1)


class NextPageButton(discord.ui.Button):
    def __init__(self, parent_view: "StatusEffectView"):
        is_last_page = parent_view.page >= parent_view.total_pages - 1
        super().__init__(label="Next ▶", style=discord.ButtonStyle.secondary, disabled=is_last_page)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.go_to_page(interaction, self.parent_view.page + 1)


class StatusEffectView(discord.ui.View):
    PAGE_SIZE = EmbedBuilder.STATUS_EFFECT_PAGE_SIZE

    def __init__(self, effect_name: str, effect_description: str, matches: list[dict], page: int = 0, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.effect_name = effect_name
        self.effect_description = effect_description
        self.matches = matches
        self.page = page
        self.total_pages = max(1, (len(matches) - 1) // self.PAGE_SIZE + 1)
        self._rebuild_items()

    def _current_page_matches(self) -> list[dict]:
        start = self.page * self.PAGE_SIZE
        return self.matches[start:start + self.PAGE_SIZE]

    def _rebuild_items(self) -> None:
        self.clear_items()
        self.add_item(PrevPageButton(self))
        self.add_item(NextPageButton(self))

        page_matches = self._current_page_matches()
        if page_matches:
            self.add_item(UnitPickSelect(page_matches, self))

    def current_embed(self) -> discord.Embed:
        return EmbedBuilder.build_status_effect_page_embed(
            self.effect_name, self.effect_description, self.matches, self.page
        )

    async def go_to_page(self, interaction: discord.Interaction, page: int) -> None:
        self.page = page
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.current_embed(), view=self)