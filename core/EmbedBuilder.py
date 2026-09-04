"""
Turns Unit/Ability/Passive/etc. objects (core/Models.py) into Discord
embeds. Nothing here touches data_loader directly for units themselves
(a Unit object is already fully resolved) -- but evolution material
names ARE looked up here via data_loader, since evolution.json only
stores material ids, not names.
"""

from pathlib import Path

import discord

import Config
from core import DataLoader, Models

# One color per enchant, so embeds are visually distinguishable at a
# glance. Add new enchants here as they're introduced. Falls back to
# a neutral color if an enchant isn't listed yet.
ENCHANT_COLORS = {
    "fire": discord.Color.orange(),
    "water": discord.Color.blue(),
    "earth": discord.Color.green(),
    "wind": discord.Color.teal(),
    "light": discord.Color.gold(),
    "dark": discord.Color.dark_purple(),
}
DEFAULT_COLOR = discord.Color.greyple()

def _resolve_local_image(path: str | None) -> Path | None:
    """Resolves a relative asset path (e.g. 'assets/units/unit_a.png')
    against the project root. Returns None if the path is a real URL,
    empty, or the file doesn't exist on disk."""
    if not path:
        return None
    full_path = Config.BASE_DIR / path
    return full_path if full_path.exists() else None


def image_file_for(path: str | None) -> discord.File | None:
    """Returns a discord.File ready to attach for a local image path,
    or None if there's nothing valid to attach."""
    resolved = _resolve_local_image(path)
    if resolved is None:
        return None
    return discord.File(resolved, filename=resolved.name)


def _set_image(embed: discord.Embed, path: str | None) -> None:
    """Sets embed.image to a real URL directly, or to the
    attachment://<filename> reference for a local file that will be
    attached alongside the embed. Does nothing if neither applies."""
    resolved = _resolve_local_image(path)
    if resolved is not None:
        embed.set_image(url=f"attachment://{resolved.name}")

def _set_thumbnail(embed: discord.Embed, path: str | None) -> None:
    """Sets embed.thumbnail to a real URL directly, or to the
    attachment://<filename> reference for a local file that will be
    attached alongside the embed. Does nothing if neither applies."""
    resolved = _resolve_local_image(path)
    if resolved is not None:
        embed.set_thumbnail(url=f"attachment://{resolved.name}")


def _color_for(enchant: str) -> discord.Color:
    return ENCHANT_COLORS.get(enchant.lower(), DEFAULT_COLOR)


def build_unit_base_embed(unit: Models.Unit) -> discord.Embed:
    embed = discord.Embed(
        title=unit.name,
        color=_color_for(unit.enchant),
    )
    if unit.tags:
            embed.description = f"`{'`, `'.join(unit.tags)}`"

    embed.add_field(name="Enchant", value=unit.enchant.title(), inline=True)

    if unit.rarity_range:
        low, high = unit.rarity_range[0], unit.rarity_range[-1]
        rarity_text = f"{low}★" if low == high else f"{low}★–{high}★"
        embed.add_field(name="Rarity", value=rarity_text, inline=True)

    if unit.basic_attack_tags:
        embed.add_field(
            name="Status Effect",
            value=", ".join(unit.basic_attack_tags),
            inline=True,
        )

    if unit.obtain_method:
        embed.add_field(name="Obtain Method", value=unit.obtain_method, inline=False)

    _set_thumbnail(embed, unit.thumbnail)

    embed.set_footer(text=f"ID: {unit.id}")
    return embed


def build_unit_evolution_embed(unit: Models.Unit) -> discord.Embed:
    embed = discord.Embed(
        title=f"{unit.name} — Evolution",
        color=_color_for(unit.enchant),
    )

    if unit.evolution is None:
        embed.description = "This unit has no evolution requirements on record."
        return embed

    reqs = unit.evolution.requirements

    if reqs.materials:
        # Resolve material ids -> display names via data_loader, so the
        # embed shows "3x Fire Shard" instead of "3x fire_shard".
        lines = []
        for material_id, qty in reqs.materials.items():
            material_raw = DataLoader.get_material(material_id)
            display_name = material_raw["name"] if material_raw else material_id
            lines.append(f"- {qty}x {display_name}")
        embed.description = f"## Materials\n{'\n'.join(lines)}"

    if reqs.kills is not None:
        embed.description += f"\n### Kills Requirement\n{reqs.kills}x kills"

    _set_image(embed, unit.evolution.image)
    _set_thumbnail(embed, unit.evolution.thumbnail)

    return embed


def build_ability_embed(ability: Models.Ability, unit_name: str | None = None) -> discord.Embed:
    title = ability.name if not unit_name else f"{unit_name} — {ability.name}"
    embed = discord.Embed(title=title, description=ability.description, color=DEFAULT_COLOR)

    if ability.tags:
            embed.description = f"`{'`, `'.join(ability.tags)}`\n\n{ability.description}"

    if ability.cooldown is not None:
        embed.add_field(name="Cooldown", value=f"{ability.cooldown}s", inline=True)

    if ability.global_cd is not None:
        embed.add_field(name="Global Cooldown", value=f"{ability.global_cd}s", inline=True)

    _set_thumbnail(embed, ability.thumbnail)

    return embed


def build_passive_embed(passive: Models.Passive, unit_name: str | None = None) -> discord.Embed:
    title = passive.name if not unit_name else f"{unit_name} — {passive.name}"
    embed = discord.Embed(title=title, description=passive.description, color=DEFAULT_COLOR)

    if passive.tags:
        embed.description = f"`{'`, `'.join(passive.tags)}`\n\n{passive.description}"
    
    if passive.cooldown is not None:
        embed.add_field(name="Cooldown", value=f"{passive.cooldown}s", inline=True)

    if passive.global_cd is not None:
        embed.add_field(name="Global Cooldown", value=f"{passive.global_cd}s", inline=True)

    # No image field for passives, per schema.
    return embed