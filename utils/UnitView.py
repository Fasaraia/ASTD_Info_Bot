"""
The interactive View attached to a unit lookup message: Base /
Evolution / Abilities / Passives tab buttons, plus an adaptive
selector for Abilities/Passives -- a plain button when there's only
one entry, a dropdown (Select) when there are multiple.
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
        await self.parent_view.show_tab(interaction, self.tab_key)


class AbilitySelect(discord.ui.Select):
    def __init__(self, abilities: list[Models.Ability], parent_view: "UnitView"):
        options = [
            discord.SelectOption(label=a.name, value=str(i))
            for i, a in enumerate(abilities)
        ]
        super().__init__(placeholder="Choose an ability...", options=options)
        self.abilities = abilities
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        ability = self.abilities[int(self.values[0])]
        embed = EmbedBuilder.build_ability_embed(ability, self.parent_view.unit.name)
        thumbnail = EmbedBuilder.image_file_for(ability.thumbnail)
        attachments = [thumbnail] if thumbnail else []
        await interaction.response.edit_message(embed=embed, view=self.parent_view, attachments=attachments)


class PassiveSelect(discord.ui.Select):
    def __init__(self, passives: list[Models.Passive], parent_view: "UnitView"):
        options = [
            discord.SelectOption(label=p.name, value=str(i))
            for i, p in enumerate(passives)
        ]
        super().__init__(placeholder="Choose a passive...", options=options)
        self.passives = passives
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        passive = self.passives[int(self.values[0])]
        embed = EmbedBuilder.build_passive_embed(passive, self.parent_view.unit.name)
        # Passives have no image field, but still clear any image left
        # over from a previous tab.
        await interaction.response.edit_message(embed=embed, view=self.parent_view, attachments=[])


class UnitView(discord.ui.View):
    """
    Attach with: await message.channel.send(embed=..., view=UnitView(unit))

    Call UnitView.initial_embed() to get the Base tab embed to send
    alongside the view on first send.
    """

    TABS = [("Base", "base"), ("Evolution", "evolution"), ("Abilities", "abilities"), ("Passives", "passives")]

    def __init__(self, unit: Models.Unit, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.unit = unit
        self.active_tab = "base"
        self._rebuild_items()

    def initial_embed(self) -> discord.Embed:
        return EmbedBuilder.build_unit_base_embed(self.unit)

    def _rebuild_items(self) -> None:
        self.clear_items()

        # Row 0: the four tab buttons, always present.
        for label, key in self.TABS:
            self.add_item(TabButton(label, key, self, active=(key == self.active_tab)))

        if self.active_tab == "abilities" and len(self.unit.abilities) > 1:
            self.add_item(AbilitySelect(self.unit.abilities, self))
        elif self.active_tab == "passives" and len(self.unit.passives) > 1:
            self.add_item(PassiveSelect(self.unit.passives, self))

    async def show_tab(self, interaction: discord.Interaction, tab_key: str) -> None:
        self.active_tab = tab_key
        self._rebuild_items()

        image_path: str | None = None

        if tab_key == "base":
            embed = EmbedBuilder.build_unit_base_embed(self.unit)
            image_path = self.unit.thumbnail

        elif tab_key == "evolution":
            embed = EmbedBuilder.build_unit_evolution_embed(self.unit)
            image_path = self.unit.evolution.thumbnail if self.unit.evolution else None

        elif tab_key == "abilities":
            if not self.unit.abilities:
                embed = discord.Embed(
                    title=f"{self.unit.name} — Abilities",
                    description="This unit has no recorded abilities.",
                )
            elif len(self.unit.abilities) == 1:
                embed = EmbedBuilder.build_ability_embed(self.unit.abilities[0], self.unit.name)
                image_path = self.unit.abilities[0].thumbnail
            else:
                embed = discord.Embed(
                    title=f"{self.unit.name} — Abilities",
                    description="Select an ability below to view its details.",
                )

        elif tab_key == "passives":
            if not self.unit.passives:
                embed = discord.Embed(
                    title=f"{self.unit.name} — Passives",
                    description="This unit has no recorded passives.",
                )
            elif len(self.unit.passives) == 1:
                embed = EmbedBuilder.build_passive_embed(self.unit.passives[0], self.unit.name)
                # no image_path -- passives have no image field, per schema
            else:
                embed = discord.Embed(
                    title=f"{self.unit.name} — Passives",
                    description="Select a passive below to view its details.",
                )

        else:
            embed = discord.Embed(title="Unknown tab")

        # Always pass attachments explicitly: [] clears any image left
        # over from a previous tab, [file] attaches this tab's image.
        image_file = EmbedBuilder.image_file_for(image_path)
        attachments = [image_file] if image_file else []
        await interaction.response.edit_message(embed=embed, view=self, attachments=attachments)