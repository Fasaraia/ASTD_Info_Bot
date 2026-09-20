"""
Generic 2+ page static view: N tabs, each showing its own static
embed (title/description/image) with no linking or dropdowns -- just
a plain embed swap. Used for Portal and Infinite Mode's Main/Rewards
pages, and reusable for any future gamemode category shaped the same
way.
"""

import discord

from core import EmbedBuilder, Models


class InfiniteTabButton(discord.ui.Button):
    def __init__(self, label: str, tab_key: str, parent_view: "InfiniteView", active: bool):
        style = discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.tab_key = tab_key
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.show_tab(interaction, self.tab_key)


class InfiniteView(discord.ui.View):
    """pages: an ordered dict of tab label -> Models.StaticGamemodeInfo,
    e.g. {"Main": info1, "Rewards": info2}."""

    def __init__(self, pages: dict[str, Models.StaticGamemodeInfo], timeout: float = 180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.active_tab = next(iter(pages))
        self._rebuild_items()

    def initial_embed(self) -> discord.Embed:
        return EmbedBuilder.build_static_gamemode_embed(self.pages[self.active_tab])

    def initial_image_path(self) -> str | None:
        return self.pages[self.active_tab].image

    def _rebuild_items(self) -> None:
        self.clear_items()
        for label in self.pages:
            self.add_item(InfiniteTabButton(label, label, self, active=(label == self.active_tab)))

    async def show_tab(self, interaction: discord.Interaction, tab_key: str) -> None:
        self.active_tab = tab_key
        self._rebuild_items()

        info = self.pages[tab_key]
        embed = EmbedBuilder.build_static_gamemode_embed(info)
        image_file = EmbedBuilder.image_file_for(info.image)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(embed=embed, view=self, attachments=attachments)