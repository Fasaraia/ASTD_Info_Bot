"""Tabbed view for data-driven zone information."""

import discord

from core import EmbedBuilder, Models


class ZoneTabButton(discord.ui.Button):
    def __init__(self, label: str, tab_key: str, parent_view: "ZonesView", active: bool):
        style = discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.tab_key = tab_key
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.show_tab(interaction, self.tab_key)


class ZonesView(discord.ui.View):
    """Displays one tab per zone, preserving the order from zones.json."""

    def __init__(
        self,
        zones: dict[str, Models.ZoneInfo],
        initial_tab: str | None = None,
        timeout: float = 180,
    ):
        if not zones:
            raise ValueError("ZonesView requires at least one zone")

        super().__init__(timeout=timeout)
        self.zones = zones
        self.active_tab = initial_tab if initial_tab in zones else next(iter(zones))
        self._rebuild_items()

    def initial_embed(self) -> discord.Embed:
        return EmbedBuilder.build_zone_embed(self.zones[self.active_tab])

    def initial_image_path(self) -> str | None:
        return self.zones[self.active_tab].image

    def _rebuild_items(self) -> None:
        self.clear_items()
        for key, zone in self.zones.items():
            self.add_item(ZoneTabButton(zone.title or key, key, self, active=(key == self.active_tab)))

    async def show_tab(self, interaction: discord.Interaction, tab_key: str) -> None:
        if tab_key not in self.zones:
            await interaction.response.send_message("That zone is no longer available.", ephemeral=True)
            return

        self.active_tab = tab_key
        self._rebuild_items()
        zone = self.zones[tab_key]
        image_file = EmbedBuilder.image_file_for(zone.image)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(
            embed=EmbedBuilder.build_zone_embed(zone),
            view=self,
            attachments=attachments,
        )
