"""
Regenerates units/units_index.json by scanning every unit's base.json
directly, instead of hand-maintaining the index file. This means the
index can never drift out of sync with what's actually on disk --
add/rename/remove a unit folder, rerun this, done.

Run standalone (from the project root, as a module -- plain
`python core/BuildIndex.py` won't find Config.py):
    python -m core.BuildIndex

Or call build_index() from a dev command (e.g. after adding new units
without wanting to restart the bot).
"""

import json
import logging

import Config

log = logging.getLogger("tdsinfobot.build_index")


def build_index() -> int:
    """Scans units/<enchant>/<unit_id>/base.json for every unit and
    writes units/units_index.json. Returns the number of units indexed."""

    if not Config.UNITS_DIR.exists():
        log.warning("Units directory not found: %s", Config.UNITS_DIR)
        return 0

    entries = []

    for enchant_dir in sorted(Config.UNITS_DIR.iterdir()):
        if not enchant_dir.is_dir():
            continue  # skip units_index.json itself

        for unit_dir in sorted(enchant_dir.iterdir()):
            if not unit_dir.is_dir():
                continue

            base_path = unit_dir / "base.json"
            if not base_path.exists():
                log.warning("Skipping %s: no base.json", unit_dir)
                continue

            try:
                with open(base_path, "r", encoding="utf-8") as f:
                    base = json.load(f)
            except json.JSONDecodeError as e:
                log.error("Invalid JSON in %s: %s", base_path, e.msg)
                continue

            unit_id = base.get("id")
            name = base.get("name")
            if not unit_id or not name:
                log.warning("Skipping %s: missing id or name in base.json", unit_dir)
                continue

            entries.append({
                "id": unit_id,
                "name": name,
                "enchant": base.get("enchant", ""),
                "rarity_range": base.get("rarity_range", []),
            })

    index_path = Config.UNITS_DIR / "units_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"units": entries}, f, indent=2, ensure_ascii=False)

    log.info("Wrote %d unit(s) to %s", len(entries), index_path)
    return len(entries)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = build_index()
    print(f"Indexed {count} unit(s) -> units/units_index.json")