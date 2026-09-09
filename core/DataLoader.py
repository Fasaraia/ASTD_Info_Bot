"""
Single source of truth for reading game data off disk.

Nothing else in the project should call open()/json.load() directly —
cogs and models go through this module. That means if storage ever
changes (JSON -> database, files move, etc.), only this file changes.

Usage:
    from core import DataLoader

    unit = DataLoader.get_unit("unit_a")
    material = DataLoader.get_material("fire_shard")
    orb = DataLoader.get_orb("orb_a")
    stages = DataLoader.get_gamemode_file("world1", "story")
"""

import json
import logging
from pathlib import Path
from typing import Any

import Config

log = logging.getLogger("tdsinfobot.data_loader")

# In-memory caches. Populated by load_all() / reload().
_units: dict[str, dict] = {}          # unit_id -> combined unit data
_units_index: list[dict] = []          # lightweight summary list, for search
_materials: dict[str, dict] = {}
_currencies: dict[str, dict] = {}
_status_effects: dict[str, dict] = {}
_codes: list[dict] = []
_cashboost: dict = {}
_orbs: dict[str, dict] = {}
_orbs_index: list[dict] = []
_gamemodes: dict[str, dict] = {}       # "world1/story" -> file contents
_misc: dict[str, dict] = {}            # "highest_dps" -> file contents

_loaded = False


def _read_json(path: Path) -> Any:
    if not path.exists():
        log.warning("Missing data file: %s", path)
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.error(
            "Invalid JSON in %s at line %d column %d: %s",
            path,
            e.lineno,
            e.colno,
            e.msg,
        )
        return None


def _load_units() -> None:
    """
    Walks units/<enchant>/<unit_id>/ and combines base + evolution +
    abilities + passives into one dict per unit, keyed by unit id.
    """
    _units.clear()

    if not Config.UNITS_DIR.exists():
        log.warning("Units directory not found: %s", Config.UNITS_DIR)
        return

    for enchant_dir in Config.UNITS_DIR.iterdir():
        if not enchant_dir.is_dir():
            continue  # skip units_index.json etc.

        for unit_dir in enchant_dir.iterdir():
            if not unit_dir.is_dir():
                continue

            base = _read_json(unit_dir / "base.json")
            if base is None:
                log.warning("Skipping %s: no base.json", unit_dir)
                continue

            unit_id = base["id"]
            _units[unit_id] = {
                "base": base,
                "evolution": _read_json(unit_dir / "evolution.json") or {},
                "abilities": _read_json(unit_dir / "abilities.json") or [],
                "passives": _read_json(unit_dir / "passives.json") or [],
            }

    log.info("Loaded %d unit(s)", len(_units))


def _load_units_index() -> None:
    global _units_index
    index_path = Config.UNITS_DIR / "units_index.json"
    data = _read_json(index_path)
    _units_index = data.get("units", []) if data else []
    log.info("Loaded units index: %d entr(y/ies)", len(_units_index))


def _load_mechanics() -> None:
    global _codes, _cashboost

    _materials.clear()
    _materials.update(_read_json(Config.MECHANICS_DIR / "materials.json") or {})

    _currencies.clear()
    _currencies.update(_read_json(Config.MECHANICS_DIR / "currencies.json") or {})

    _status_effects.clear()
    _status_effects.update(
        _read_json(Config.MECHANICS_DIR / "status_effects.json") or {}
    )

    codes_data = _read_json(Config.MECHANICS_DIR / "codes.json") or {}
    _codes = codes_data.get("codes", [])

    _cashboost = _read_json(Config.MECHANICS_DIR / "cashboost.json") or {}

    log.info(
        "Loaded mechanics: %d material(s), %d currenc(y/ies), "
        "%d status effect(s), %d code(s)",
        len(_materials), len(_currencies), len(_status_effects), len(_codes),
    )


def _load_orbs() -> None:
    global _orbs_index
    _orbs.clear()

    orbs_dir = Config.MECHANICS_DIR / "orbs"
    if not orbs_dir.exists():
        log.warning("Orbs directory not found: %s", orbs_dir)
        return

    for orb_file in orbs_dir.glob("*.json"):
        if orb_file.name == "orbs_index.json":
            continue
        orb = _read_json(orb_file)
        if orb and "id" in orb:
            _orbs[orb["id"]] = orb

    index_data = _read_json(orbs_dir / "orbs_index.json")
    _orbs_index = index_data.get("orbs", []) if index_data else []

    log.info("Loaded %d orb(s)", len(_orbs))


def _load_gamemodes() -> None:
    _gamemodes.clear()

    if not Config.GAMEMODES_DIR.exists():
        log.warning("Gamemodes directory not found: %s", Config.GAMEMODES_DIR)
        return

    for world_dir in Config.GAMEMODES_DIR.iterdir():
        if not world_dir.is_dir():
            continue
        for file in world_dir.glob("*.json"):
            key = f"{world_dir.name}/{file.stem}"  # e.g. "world1/story"
            _gamemodes[key] = _read_json(file) or {}

    log.info("Loaded %d gamemode file(s)", len(_gamemodes))


def _load_misc() -> None:
    _misc.clear()

    if not Config.MISC_DIR.exists():
        log.warning("Misc directory not found: %s", Config.MISC_DIR)
        return

    for file in Config.MISC_DIR.glob("*.json"):
        _misc[file.stem] = _read_json(file) or {}

    log.info("Loaded %d misc file(s)", len(_misc))


def load_all() -> None:
    """Load (or reload) every data category from disk into memory."""
    global _loaded
    _load_units()
    _load_units_index()
    _load_mechanics()
    _load_orbs()
    _load_gamemodes()
    _load_misc()
    _loaded = True
    log.info("Data load complete.")


def reload() -> None:
    """Alias for load_all() — call this from a dev command after editing JSON."""
    load_all()


def _ensure_loaded() -> None:
    if not _loaded:
        load_all()


# --- Public getters ---

def get_unit(unit_id: str) -> dict | None:
    _ensure_loaded()
    return _units.get(unit_id)


def list_units_index() -> list[dict]:
    _ensure_loaded()
    return _units_index


def get_material(material_id: str) -> dict | None:
    _ensure_loaded()
    return _materials.get(material_id)


def get_currency(currency_id: str) -> dict | None:
    _ensure_loaded()
    return _currencies.get(currency_id)


def get_status_effect(effect_id: str) -> dict | None:
    _ensure_loaded()
    return _status_effects.get(effect_id)


def find_status_effect_id_by_name(name: str) -> str | None:
    """Case-insensitive match against each status effect's display
    'name' field, returning its internal id (e.g. 'Bleed' -> 'bleed').
    Status effect ids are expected to be unique (they're dict keys),
    so at most one match exists."""
    _ensure_loaded()
    target = name.lower()

    for effect_id, effect in _status_effects.items():
        if effect.get("name", "").lower() == target:
            return effect_id

    return None


def get_codes() -> list[dict]:
    _ensure_loaded()
    return _codes


def get_cashboost() -> dict:
    _ensure_loaded()
    return _cashboost


def get_orb(orb_id: str) -> dict | None:
    _ensure_loaded()
    return _orbs.get(orb_id)


def list_orbs_index() -> list[dict]:
    _ensure_loaded()
    return _orbs_index


def get_gamemode_file(world: str, name: str) -> dict:
    """e.g. get_gamemode_file("world1", "story")"""
    _ensure_loaded()
    return _gamemodes.get(f"{world}/{name}", {})


def get_misc(name: str) -> dict:
    """e.g. get_misc("highest_dps")"""
    _ensure_loaded()
    return _misc.get(name, {})


def find_units_by_status_effect(effect_id: str) -> list[dict]:
    """
    Scans every unit's basic_attack_tags, ability tags, and passive tags
    for a given status effect id. Returns a list of matches, each noting
    which source(s) applied it.
    """
    _ensure_loaded()
    results = []

    for unit_id, unit in _units.items():
        sources = []

        if effect_id in unit["base"].get("basic_attack_tags", []):
            sources.append("basic attack")

        for ability in unit.get("abilities", []):
            if effect_id in ability.get("tags", []):
                sources.append(f"ability: {ability['name']}")

        for passive in unit.get("passives", []):
            if effect_id in passive.get("tags", []):
                sources.append(f"passive: {passive['name']}")

        if sources:
            results.append({
                "unit_id": unit_id,
                "name": unit["base"]["name"],
                "sources": sources,
            })

    return results


def find_ability_owners(ability_name: str) -> list[tuple[str, int]]:
    """
    Case-insensitive exact match against every unit's ability names.
    Returns a list of (unit_id, ability_index) for EVERY match, since
    multiple units can share the same ability name -- callers decide
    how to handle 0, 1, or multiple results.
    """
    _ensure_loaded()
    target = ability_name.lower()
    matches = []

    for unit_id, unit in _units.items():
        for i, ability in enumerate(unit.get("abilities", [])):
            if ability.get("name", "").lower() == target:
                matches.append((unit_id, i))

    return matches


def find_passive_owners(passive_name: str) -> list[tuple[str, int]]:
    """
    Case-insensitive exact match against every unit's passive names.
    Returns a list of (unit_id, passive_index) for EVERY match, since
    multiple units can share the same passive name -- callers decide
    how to handle 0, 1, or multiple results.
    """
    _ensure_loaded()
    target = passive_name.lower()
    matches = []

    for unit_id, unit in _units.items():
        for i, passive in enumerate(unit.get("passives", [])):
            if passive.get("name", "").lower() == target:
                matches.append((unit_id, i))

    return matches


def get_raids(world: str) -> list[dict]:
    """Raw raid entries for a world, e.g. get_raids('world2')."""
    data = get_gamemode_file(world, "raids")
    return data.get("raids", [])


def find_raids_by_enchant(world: str, enchant: str) -> list[dict]:
    """Case-insensitive match against each raid's enchant field."""
    target = enchant.lower()
    return [r for r in get_raids(world) if (r.get("enchant") or "").lower() == target]


def find_raids_by_drop(world: str, item_name: str) -> list[dict]:
    """Every raid in `world` whose drops list contains an item matching
    item_name (case-insensitive)."""
    target = item_name.lower()
    matches = []
    for raid in get_raids(world):
        for drop in raid.get("drops", []):
            if drop.get("name", "").lower() == target:
                matches.append(raid)
                break
    return matches


def find_material_id_by_name(name: str) -> str | None:
    """Case-insensitive match against each material's display 'name'
    field, returning its internal id."""
    _ensure_loaded()
    target = name.lower()
    for material_id, material in _materials.items():
        if material.get("name", "").lower() == target:
            return material_id
    return None


def find_units_needing_material(material_id: str) -> list[dict]:
    """Every unit whose evolution.requirements.materials references
    material_id. Returns [{"unit_id": ..., "name": ...}, ...]."""
    _ensure_loaded()
    matches = []

    for unit_id, unit in _units.items():
        evolution = unit.get("evolution") or {}
        requirements = evolution.get("requirements", {}) or {}
        materials = requirements.get("materials", {}) or {}
        if material_id in materials:
            matches.append({"unit_id": unit_id, "name": unit["base"]["name"]})

    return matches


def find_story_stages_by_drop(item_name: str) -> list[dict]:
    """Every story chapter (across both World 1 and World 2) whose
    drops include item_name. Each result dict is the raw chapter data
    with a 'world' and 'world_label' key merged in."""
    target = item_name.lower()
    matches = []

    for world, world_label in (("world1", "World 1"), ("world2", "World 2")):
        data = get_gamemode_file(world, "story")
        for chapter in data.get("chapters", []):
            for drop in chapter.get("drops", []):
                if drop.get("name", "").lower() == target:
                    matches.append({**chapter, "world": world, "world_label": world_label})
                    break

    return matches


def find_trial_stages_by_drop(item_name: str) -> list[dict]:
    """Every trial stage (World 1 only -- World 2 has no trials) whose
    drops include item_name. Each result dict is the raw stage data
    with a 'world_label' key merged in."""
    target = item_name.lower()
    matches = []

    data = get_gamemode_file("world1", "trials")
    for stage in data.get("stages", []):
        for drop in stage.get("drops", []):
            if drop.get("name", "").lower() == target:
                matches.append({**stage, "world_label": "World 1"})
                break

    return matches