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
# glance. Falls back to a neutral color if a unit has no enchant or
# one not listed here.
ENCHANT_COLORS = {
    "fire": discord.Color.orange(),
    "nature": discord.Color.green(),
    "earth": discord.Color.dark_gold(),
    "wind": discord.Color.teal(),
    "dark": discord.Color.dark_purple(),
    "holy": discord.Color.gold(),
}

# Single-letter abbreviation shown in brackets in stage listings, e.g.
# "Familiar Planet[F]". Stages/units with no enchant show no bracket.
ENCHANT_LETTERS = {
    "fire": "F",
    "nature": "N",
    "earth": "E",
    "wind": "W",
    "dark": "D",
    "holy": "H",
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


def image_files_for(*paths: str | None) -> list[discord.File]:
    """Resolves several local image paths at once (e.g. an evolution's
    image + thumbnail) into a list of discord.File, skipping anything
    invalid and de-duplicating by filename so the same file is never
    attached twice."""
    files: list[discord.File] = []
    seen_names: set[str] = set()

    for path in paths:
        resolved = _resolve_local_image(path)
        if resolved is None or resolved.name in seen_names:
            continue
        seen_names.add(resolved.name)
        files.append(discord.File(resolved, filename=resolved.name))

    return files


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


def _format_amount(amount: tuple[int, int]) -> str:
    """[1, 1] -> 'x1' (exact count), [1, 3] -> 'x1-3' (range). Same
    field either way -- the display just reflects what's stored."""
    low, high = amount[0], amount[-1]
    return f"x{low}" if low == high else f"x{low}-{high}"


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


def build_story_overview_embed(world_label: str, chapters: list[Models.StoryChapter]) -> discord.Embed:
    """One line per chapter, e.g.:
    22. Familiar Planet[F] (127-132) — Strong Alien Soldier 1-3
    """
    embed = discord.Embed(title=f"{world_label} Story Stages", color=DEFAULT_COLOR)

    if not chapters:
        embed.description = "No story stages on record yet."
        return embed

    lines = []
    for ch in chapters:
        letter = ENCHANT_LETTERS.get(ch.enchant.lower()) if ch.enchant else None
        enchant_part = f"[{letter}]" if letter else ""
        act_part = f"({ch.act_range[0]}-{ch.act_range[1]})"
        drop_part = ", ".join(f"{d.name} {d.range[0]}-{d.range[1]}" for d in ch.drops)
        lines.append(f"{ch.stage_number}. **{ch.name}**{enchant_part} {act_part} — {drop_part}")

    embed.description = "\n".join(lines)
    return embed


def build_story_chapter_embed(world_label: str, chapter: Models.StoryChapter) -> discord.Embed:
    title = f"{world_label} — {chapter.name}"
    embed = discord.Embed(title=title, color=DEFAULT_COLOR)

    if chapter.enchant:
        embed.add_field(name="Enchant", value=chapter.enchant.title(), inline=True)

    embed.add_field(
        name="Acts", value=f"{chapter.act_range[0]}–{chapter.act_range[1]}", inline=True
    )

    if chapter.drops:
        drop_lines = "\n".join(f"{d.name} {d.range[0]}-{d.range[1]}" for d in chapter.drops)
        embed.add_field(name="Drops", value=drop_lines, inline=True)

    if chapter.description:
        embed.description = chapter.description

    _set_image(embed, chapter.image)
    return embed


def build_trials_overview_embed(world_label: str, stages: list[Models.TrialStage]) -> discord.Embed:
    """
    One numbered line per trial stage, same style as the story overview
    but with no act range, e.g.:
    1. Ashfall Trial[F] — Trial Guardian 1-3
    """
    embed = discord.Embed(title=f"{world_label} Trials", color=DEFAULT_COLOR)

    if not stages:
        embed.description = "No trial stages on record yet."
        return embed

    lines = []
    for stage in stages:
        letter = ENCHANT_LETTERS.get(stage.enchant.lower()) if stage.enchant else None
        enchant_part = f"[{letter}]" if letter else ""
        drop_part = ", ".join(f"{d.name} {d.range[0]}-{d.range[1]}" for d in stage.drops)
        lines.append(f"{stage.stage_number}. **{stage.name}**{enchant_part} — {drop_part}")

    embed.description = "\n".join(lines)
    return embed


def build_trial_stage_embed(world_label: str, stage: Models.TrialStage) -> discord.Embed:
    title = f"{world_label} — {stage.name}"
    embed = discord.Embed(title=title, color=DEFAULT_COLOR)

    if stage.enchant:
        embed.add_field(name="Enchant", value=stage.enchant.title(), inline=True)

    if stage.drops:
        drop_lines = "\n".join(f"{d.name} {d.range[0]}-{d.range[1]}" for d in stage.drops)
        embed.add_field(name="Drops", value=drop_lines, inline=True)

    if stage.description:
        embed.description = stage.description

    _set_image(embed, stage.image)
    return embed


STATUS_EFFECT_PAGE_SIZE = 25


def build_status_effect_page_embed(
    effect_name: str, effect_description: str, matches: list[dict], page: int
) -> discord.Embed:

    embed = discord.Embed(title=f"Units with {effect_name}", color=DEFAULT_COLOR)

    if effect_description:
        embed.description = effect_description

    if not matches:
        embed.add_field(name="Results", value="No units apply this status effect.", inline=False)
        return embed

    total_pages = max(1, (len(matches) - 1) // STATUS_EFFECT_PAGE_SIZE + 1)
    start = page * STATUS_EFFECT_PAGE_SIZE
    page_matches = matches[start:start + STATUS_EFFECT_PAGE_SIZE]

    lines = []
    for match in page_matches:
        sources = ", ".join(match["sources"])
        lines.append(f"**{match['name']}** — {sources}")

    embed.add_field(name="Units", value="\n".join(lines), inline=False)
    embed.set_footer(text=f"Page {page + 1}/{total_pages} — {len(matches)} unit(s) total")
    return embed


def build_raids_overview_embed(world_label: str, enchant_label: str, raids: list[Models.Raid]) -> discord.Embed:
    embed = discord.Embed(title=f"{world_label} — {enchant_label} Raids", color=DEFAULT_COLOR)

    if not raids:
        embed.description = f"No {enchant_label.lower()} raids on record yet."
        return embed

    lines = []
    for i, raid in enumerate(raids, start=1):
        drop_part = ", ".join(f"{d.name} {_format_amount(d.amount)}" for d in raid.drops)
        lines.append(f"{i}. **{raid.name}** — {drop_part}")

    embed.description = "\n".join(lines)
    return embed


def build_raid_detail_embed(world_label: str, raid: Models.Raid) -> discord.Embed:
    embed = discord.Embed(title=f"{world_label} — {raid.name}", color=DEFAULT_COLOR)

    if raid.enchant:
        embed.add_field(name="Enchant", value=raid.enchant.title(), inline=True)

    if raid.drops:
        drop_lines = "\n".join(f"{d.name} `{_format_amount(d.amount)}`" for d in raid.drops)
        embed.add_field(name="Drops", value=drop_lines, inline=True)

    _set_image(embed, raid.image)
    return embed


def build_raid_drop_matches_embed(item_name: str, raids: list[Models.Raid]) -> discord.Embed:
    embed = discord.Embed(title=f"Raids dropping {item_name}", color=DEFAULT_COLOR)

    if not raids:
        embed.add_field(name="Results", value="No raids drop this item.", inline=False)
        return embed

    lines = [f"**{r.name}**" for r in raids]
    embed.add_field(name="Raids", value="\n".join(lines), inline=False)
    return embed


def build_story_drop_matches_embed(item_name: str, chapters: list[Models.StoryChapter]) -> discord.Embed:
    embed = discord.Embed(title=f"Story stages dropping {item_name}", color=DEFAULT_COLOR)
    if not chapters:
        embed.add_field(name="Results", value="No story stages drop this item.", inline=False)
        return embed
    lines = [f"**{ch.name}**" for ch in chapters]
    embed.add_field(name="Stages", value="\n".join(lines), inline=False)
    return embed


def build_trial_drop_matches_embed(item_name: str, stages: list[Models.TrialStage]) -> discord.Embed:
    embed = discord.Embed(title=f"Trials dropping {item_name}", color=DEFAULT_COLOR)
    if not stages:
        embed.add_field(name="Results", value="No trial stages drop this item.", inline=False)
        return embed
    lines = [f"**{s.name}**" for s in stages]
    embed.add_field(name="Stages", value="\n".join(lines), inline=False)
    return embed


def build_unit_material_matches_embed(item_name: str, units: list[dict]) -> discord.Embed:
    """units: [{"unit_id": ..., "name": ...}]"""
    embed = discord.Embed(title=f"Units requiring {item_name}", color=DEFAULT_COLOR)
    if not units:
        embed.add_field(name="Results", value="No units require this material.", inline=False)
        return embed
    lines = [f"**{u['name']}**" for u in units]
    embed.add_field(name="Units", value="\n".join(lines), inline=False)
    return embed


def build_item_usage_picker_embed(item_name: str, source_counts: dict[str, int]) -> discord.Embed:
    """source_counts: {"Raids": 2, "Units": 3, ...} -- only sources
    with at least one match should be included."""
    embed = discord.Embed(title=f"\"{item_name}\" found in multiple places", color=DEFAULT_COLOR)
    lines = [f"**{source}** — {count} match(es)" for source, count in source_counts.items()]
    embed.description = "\n".join(lines) + "\n\nPick a category below:"
    return embed


def build_unit_choice_embed(unit_name: str) -> discord.Embed:
    """The initial chooser shown when a unit is looked up directly by
    name: pick between viewing the unit itself or where it's
    obtainable from."""
    embed = discord.Embed(title=unit_name)
    embed.description = "What would you like to view?"
    return embed


def build_unit_obtainable_embed(
    unit_name: str,
    raids: list[Models.Raid],
    story_chapters: list[Models.StoryChapter],
    trial_stages: list[Models.TrialStage],
) -> discord.Embed:
    """Reverse lookup: everywhere a drop matching unit_name shows up
    across Raids, Story, and Trials."""
    embed = discord.Embed(title=f"{unit_name} — Obtainable From", color=DEFAULT_COLOR)

    if not raids and not story_chapters and not trial_stages:
        embed.description = "Not currently obtainable from any recorded raid, story stage, or trial."
        return embed

    if raids:
        embed.add_field(name="Raids", value="\n".join(f"**{r.name}**" for r in raids), inline=False)
    if story_chapters:
        embed.add_field(name="Story", value="\n".join(f"**{c.name}**" for c in story_chapters), inline=False)
    if trial_stages:
        embed.add_field(name="Trials", value="\n".join(f"**{s.name}**" for s in trial_stages), inline=False)

    return embed