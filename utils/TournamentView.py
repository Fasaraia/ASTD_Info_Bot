"""
The interactive View for Tournament Mode: Main / Local Rewards /
Global Rewards / Previous Rewards tabs (mirrors UnitView's tab
pattern). Each Rewards tab lists every reward in that tier and, if
there's at least one, shows a dropdown to jump straight to any
reward's own page (unit page, material card, currency card, or orb
card) -- with a Back button returning to that rewards tab.
"""

import discord

from core import DataLoader, EmbedBuilder, Models
from utils.UnitView import BackButton, UnitView
from utils.OrbView import OrbView


class TabButton(discord.ui.Button):
    def __init__(self, label: str, tab_key: str, parent_view: "TournamentView", active: bool):
        style = discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.tab_key = tab_key
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.show_tab(interaction, self.tab_key)


class RewardSelect(discord.ui.Select):
    """Flattens units/materials/currencies/orbs for one rewards tier
    into a single dropdown -- picking any entry opens that thing's own
    page directly, with Back pointing at this rewards tab."""

    def __init__(self, rewards: Models.TournamentRewards, parent_view: "TournamentView"):
        self.entries: list[tuple[str, str]] = []  # (type, id)
        options = []

        for unit_id in rewards.units:
            raw = DataLoader.get_unit(unit_id)
            name = raw["base"]["name"] if raw else unit_id
            options.append(discord.SelectOption(label=f"{name} (Unit)", value=str(len(self.entries))))
            self.entries.append(("unit", unit_id))

        for material_id in rewards.materials:
            raw = DataLoader.get_material(material_id)
            name = raw["name"] if raw else material_id
            options.append(discord.SelectOption(label=f"{name} (Material)", value=str(len(self.entries))))
            self.entries.append(("material", material_id))

        for currency_id in rewards.currencies:
            raw = DataLoader.get_currency(currency_id)
            name = raw["name"] if raw else currency_id
            options.append(discord.SelectOption(label=f"{name} (Currency)", value=str(len(self.entries))))
            self.entries.append(("currency", currency_id))

        for orb_id in rewards.orbs:
            raw = DataLoader.get_orb(orb_id)
            name = raw["name"] if raw else orb_id
            options.append(discord.SelectOption(label=f"{name} (Orb)", value=str(len(self.entries))))
            self.entries.append(("orb", orb_id))

        super().__init__(placeholder="View a specific reward...", options=options[:25])
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        entry_type, entry_id = self.entries[int(self.values[0])]
        back_embed, back_view = self.parent_view.current_rewards_embed, self.parent_view

        if entry_type == "unit":
            raw = DataLoader.get_unit(entry_id)
            if raw is None:
                await interaction.response.edit_message(content="That unit's data could not be found.", embed=None, view=None)
                return
            unit = Models.Unit.from_raw(raw)
            view = UnitView(unit, back_embed=back_embed, back_view=back_view)
            embed = view.initial_embed()
            files = EmbedBuilder.image_files_for(*view.initial_image_paths())
            await interaction.response.edit_message(embed=embed, view=view, attachments=files)

        elif entry_type == "material":
            raw = DataLoader.get_material(entry_id)
            material = Models.Material.from_raw(entry_id, raw or {})
            embed = EmbedBuilder.build_material_detail_embed(material)
            view = discord.ui.View(timeout=180)
            view.add_item(BackButton(back_embed, back_view))
            image_file = EmbedBuilder.image_file_for(material.image)
            files = [image_file] if image_file else []
            await interaction.response.edit_message(embed=embed, view=view, attachments=files)

        elif entry_type == "currency":
            raw = DataLoader.get_currency(entry_id)
            currency = Models.Currency.from_raw(entry_id, raw or {})
            embed = EmbedBuilder.build_currency_detail_embed(currency)
            view = discord.ui.View(timeout=180)
            view.add_item(BackButton(back_embed, back_view))
            image_file = EmbedBuilder.image_file_for(currency.image)
            files = [image_file] if image_file else []
            await interaction.response.edit_message(embed=embed, view=view, attachments=files)

        elif entry_type == "orb":
            raw = DataLoader.get_orb(entry_id)
            if raw is None:
                await interaction.response.edit_message(content="That orb's data could not be found.", embed=None, view=None)
                return
            orb = Models.Orb.from_raw(raw)
            view = OrbView(orb, back_embed=back_embed, back_view=back_view)
            image_file = EmbedBuilder.image_file_for(orb.image)
            files = [image_file] if image_file else []
            await interaction.response.edit_message(embed=view.embed, view=view, attachments=files)


class TournamentView(discord.ui.View):
    TABS = [
        ("Main", "main"),
        ("Local Rewards", "local"),
        ("Global Rewards", "global"),
        ("Previous Rewards", "previous"),
    ]

    def __init__(self, tournament: Models.Tournament, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.tournament = tournament
        self.active_tab = "main"
        self.current_rewards_embed: discord.Embed | None = None
        self._rebuild_items()

    def _rewards_for(self, tab_key: str) -> Models.TournamentRewards | None:
        return {
            "local": self.tournament.local_rewards,
            "global": self.tournament.global_rewards,
            "previous": self.tournament.previous_rewards,
        }.get(tab_key)

    def initial_embed(self) -> discord.Embed:
        return EmbedBuilder.build_tournament_main_embed(self.tournament)

    def _rebuild_items(self) -> None:
        self.clear_items()

        for label, key in self.TABS:
            self.add_item(TabButton(label, key, self, active=(key == self.active_tab)))

        rewards = self._rewards_for(self.active_tab)
        if rewards is not None:
            has_any = rewards.units or rewards.materials or rewards.currencies or rewards.orbs
            if has_any:
                self.add_item(RewardSelect(rewards, self))

    async def show_tab(self, interaction: discord.Interaction, tab_key: str) -> None:
        self.active_tab = tab_key
        self._rebuild_items()

        if tab_key == "main":
            embed = EmbedBuilder.build_tournament_main_embed(self.tournament)
            image_path = self.tournament.image
        else:
            label_map = {"local": "Local Rewards", "global": "Global Rewards", "previous": "Previous Rewards"}
            rewards = self._rewards_for(tab_key)
            embed = EmbedBuilder.build_tournament_rewards_embed(label_map[tab_key], rewards)
            self.current_rewards_embed = embed
            image_path = None

        image_file = EmbedBuilder.image_file_for(image_path)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(embed=embed, view=self, attachments=attachments)