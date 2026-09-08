"""
The interactive View attached to a unit lookup message: Base /
Evolution / Abilities / Passives tab buttons, plus an adaptive
selector for Abilities/Passives -- a plain button when there's only
one entry, a dropdown (Select) when there are multiple.

Supports opening directly to a specific ability/passive (used when a
person triggers an ability/passive by its own name rather than the
unit's name) -- the matching tab opens showing that entry immediately,
with the dropdown (if present) pre-selected to it.
"""

import discord

from core import EmbedBuilder, Models


class TabButton(discord.ui.Button):
    def __init__(self, label: str, tab_key: str, parent_view: "UnitView", active: bool):
        style = discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.tab_key = tab_key
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # A plain tab click resets to that tab's default state -- no
        # specific ability/passive pre-selected.
        await self.parent_view.show_tab(interaction, self.tab_key, index=None)


class AbilitySelect(discord.ui.Select):
    def __init__(self, abilities: list[Models.Ability], parent_view: "UnitView", selected_index: int | None):
        options = [
            discord.SelectOption(label=a.name, value=str(i), default=(i == selected_index))
            for i, a in enumerate(abilities)
        ]
        super().__init__(placeholder="Choose an ability...", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        await self.parent_view.show_tab(interaction, "abilities", index=idx)


class PassiveSelect(discord.ui.Select):
    def __init__(self, passives: list[Models.Passive], parent_view: "UnitView", selected_index: int | None):
        options = [
            discord.SelectOption(label=p.name, value=str(i), default=(i == selected_index))
            for i, p in enumerate(passives)
        ]
        super().__init__(placeholder="Choose a passive...", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        await self.parent_view.show_tab(interaction, "passives", index=idx)


class BackButton(discord.ui.Button):
    """Returns to whatever embed+view this UnitView was opened from
    (e.g. an ability/passive disambiguation picker, or a status effect
    results page). Only added when a UnitView is given a back_target."""

    def __init__(self, back_embed: discord.Embed, back_view: discord.ui.View):
        super().__init__(label="◀ Back", style=discord.ButtonStyle.secondary)
        self.back_embed = back_embed
        self.back_view = back_view

    async def callback(self, interaction: discord.Interaction):
        # Clear attachments explicitly -- the unit embed we're leaving
        # may have had an image/thumbnail attached; the page we're
        # returning to never does.
        await interaction.response.edit_message(embed=self.back_embed, view=self.back_view, attachments=[])


class UnitView(discord.ui.View):
    """
    Attach with:
        view = UnitView(unit)  # opens on the Base tab
        await message.channel.send(embed=view.initial_embed(), view=view)

    To open directly on a specific ability/passive (name-triggered
    lookup), pass initial_tab + initial_index:
        view = UnitView(unit, initial_tab="abilities", initial_index=2)
    """

    TABS = [("Base", "base"), ("Evolution", "evolution"), ("Abilities", "abilities"), ("Passives", "passives")]

    def __init__(
        self,
        unit: Models.Unit,
        initial_tab: str = "base",
        initial_index: int | None = None,
        back_embed: discord.Embed | None = None,
        back_view: discord.ui.View | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.unit = unit
        self.active_tab = initial_tab
        self.active_index = initial_index
        self.back_embed = back_embed
        self.back_view = back_view
        self._rebuild_items()

    def initial_embed(self) -> discord.Embed:
        embed, _ = self._build_display(self.active_tab, self.active_index)
        return embed

    def initial_image_paths(self) -> list[str | None]:
        _, paths = self._build_display(self.active_tab, self.active_index)
        return paths

    def _rebuild_items(self) -> None:
        self.clear_items()

        # Row 0: the four tab buttons, plus a 5th "Back" button when
        # this view was opened from a disambiguation picker or a
        # status effect results page (5 buttons max per row, so this
        # fits exactly).
        for label, key in self.TABS:
            self.add_item(TabButton(label, key, self, active=(key == self.active_tab)))

        if self.back_embed is not None and self.back_view is not None:
            self.add_item(BackButton(self.back_embed, self.back_view))

        if self.active_tab == "abilities" and len(self.unit.abilities) > 1:
            self.add_item(AbilitySelect(self.unit.abilities, self, self.active_index))
        elif self.active_tab == "passives" and len(self.unit.passives) > 1:
            self.add_item(PassiveSelect(self.unit.passives, self, self.active_index))

    def _build_display(self, tab_key: str, index: int | None) -> tuple[discord.Embed, list[str | None]]:
        """Returns (embed, image_paths) for a tab + optional specific
        ability/passive index. image_paths may contain None entries --
        EmbedBuilder.image_files_for() filters those out."""

        if tab_key == "base":
            embed = EmbedBuilder.build_unit_base_embed(self.unit)
            return embed, [self.unit.thumbnail]

        if tab_key == "evolution":
            embed = EmbedBuilder.build_unit_evolution_embed(self.unit)
            if self.unit.evolution:
                # Both the large image AND the thumbnail need attaching.
                return embed, [self.unit.evolution.image, self.unit.evolution.thumbnail]
            return embed, []

        if tab_key == "abilities":
            abilities = self.unit.abilities
            if not abilities:
                return discord.Embed(
                    title=f"{self.unit.name} — Abilities",
                    description="This unit has no recorded abilities.",
                ), []
            if len(abilities) == 1:
                return EmbedBuilder.build_ability_embed(abilities[0], self.unit.name), [abilities[0].thumbnail]
            if index is not None:
                ability = abilities[index]
                return EmbedBuilder.build_ability_embed(ability, self.unit.name), [ability.thumbnail]
            return discord.Embed(
                title=f"{self.unit.name} — Abilities",
                description="Select an ability below to view its details.",
            ), []

        if tab_key == "passives":
            passives = self.unit.passives
            if not passives:
                return discord.Embed(
                    title=f"{self.unit.name} — Passives",
                    description="This unit has no recorded passives.",
                ), []
            if len(passives) == 1:
                return EmbedBuilder.build_passive_embed(passives[0], self.unit.name), []
            if index is not None:
                passive = passives[index]
                return EmbedBuilder.build_passive_embed(passive, self.unit.name), []
            return discord.Embed(
                title=f"{self.unit.name} — Passives",
                description="Select a passive below to view its details.",
            ), []

        return discord.Embed(title="Unknown tab"), []

    async def show_tab(self, interaction: discord.Interaction, tab_key: str, index: int | None = None) -> None:
        self.active_tab = tab_key
        self.active_index = index
        self._rebuild_items()

        embed, image_paths = self._build_display(tab_key, index)
        files = EmbedBuilder.image_files_for(*image_paths)

        # Always pass attachments explicitly: [] clears any image(s)
        # left over from a previous tab.
        await interaction.response.edit_message(embed=embed, view=self, attachments=files)