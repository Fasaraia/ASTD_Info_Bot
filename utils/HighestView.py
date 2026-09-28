import discord

from core import EmbedBuilder


class HighestDPSView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=300)
        self.data = data
        self.page = "raid"

        self._update_buttons()

    def _update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = child.custom_id == self.page

    def embed(self):
        return EmbedBuilder.build_highest_dps_embed(
            self.data,
            self.page
        )

    async def _change_page(
        self,
        interaction: discord.Interaction,
        page: str
    ):
        self.page = page
        self._update_buttons()

        await interaction.response.edit_message(
            embed=self.embed(),
            view=self
        )

    @discord.ui.button(
        label="Raid",
        custom_id="raid"
    )
    async def raid_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self._change_page(interaction, "raid")

    @discord.ui.button(
        label="Max",
        custom_id="max"
    )
    async def max_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self._change_page(interaction, "max")

    @discord.ui.button(
        label="DOT",
        custom_id="dot"
    )
    async def dot_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self._change_page(interaction, "dot")


class HighestNukesView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=300)
        self.data = data
        self.page = "raid"

        self._update_buttons()

    def _update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = child.custom_id == self.page

    def embed(self):
        return EmbedBuilder.build_highest_nukes_embed(
            self.data,
            self.page
        )

    async def _change_page(
        self,
        interaction: discord.Interaction,
        page: str
    ):
        self.page = page
        self._update_buttons()

        await interaction.response.edit_message(
            embed=self.embed(),
            view=self
        )

    @discord.ui.button(
        label="Raid",
        style=discord.ButtonStyle.primary,
        custom_id="raid"
    )
    async def raid_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self._change_page(interaction, "raid")

    @discord.ui.button(
        label="Max",
        style=discord.ButtonStyle.secondary,
        custom_id="max"
    )
    async def max_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self._change_page(interaction, "max")