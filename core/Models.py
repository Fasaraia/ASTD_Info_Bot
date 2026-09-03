"""
Typed wrappers around the raw dicts data_loader returns.

Usage:
    from core import data_loader, models

    raw = data_loader.get_unit("unit_a")
    unit = models.Unit.from_raw(raw)
    print(unit.name, unit.abilities[0].name)
"""

from dataclasses import dataclass, field


@dataclass
class Ability:
    name: str
    description: str
    cooldown: int | None
    global_cd: int | None
    tags: list[str] = field(default_factory=list)
    thumbnail: str | None = None

    @classmethod
    def from_raw(cls, raw: dict) -> "Ability":
        return cls(
            name=raw.get("name", "Unknown Ability"),
            description=raw.get("description", ""),
            cooldown=raw.get("cooldown"),
            global_cd=raw.get("global_cd"),
            tags=raw.get("tags", []),
            thumbnail=raw.get("thumbnail"),
        )


@dataclass
class Passive:
    name: str
    description: str
    cooldown: int | None
    global_cd: int | None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict) -> "Passive":
        return cls(
            name=raw.get("name", "Unknown Passive"),
            description=raw.get("description", ""),
            cooldown=raw.get("cooldown"),
            global_cd=raw.get("global_cd"),
            tags=raw.get("tags", []),
        )


@dataclass
class EvolutionRequirements:
    materials: dict[str, int] = field(default_factory=dict)
    kills: int | None = None

    @classmethod
    def from_raw(cls, raw: dict) -> "EvolutionRequirements":
        conditions = raw.get("conditions", {}) or {}
        return cls(
            materials=raw.get("materials", {}) or {},
            kills=conditions.get("kills"),
        )


@dataclass
class Evolution:
    requirements: EvolutionRequirements
    image: str | None = None
    thumbnail: str | None = None

    @classmethod
    def from_raw(cls, raw: dict) -> "Evolution":
        return cls(
            requirements=EvolutionRequirements.from_raw(raw.get("requirements", {})),
            image=raw.get("image"),
            thumbnail=raw.get("thumbnail")
        )


@dataclass
class Unit:
    id: str
    name: str
    tags: list[str]
    enchant: str
    rarity_range: list[int]
    evolution_line: list[str]
    obtain_method: str
    basic_attack_tags: list[str]
    thumbnail: str | None
    evolution: Evolution | None
    abilities: list[Ability]
    passives: list[Passive]

    @classmethod
    def from_raw(cls, raw: dict) -> "Unit":
        base = raw.get("base", {})

        evolution_raw = raw.get("evolution")
        evolution = Evolution.from_raw(evolution_raw) if evolution_raw else None

        abilities = [Ability.from_raw(a) for a in raw.get("abilities", [])]
        passives = [Passive.from_raw(p) for p in raw.get("passives", [])]

        return cls(
            id=base.get("id", ""),
            name=base.get("name", "Unknown Unit"),
            tags=base.get("tags", []),
            enchant=base.get("enchant", ""),
            rarity_range=base.get("rarity_range", []),
            evolution_line=base.get("evolution_line", []),
            obtain_method=base.get("obtain_method", ""),
            basic_attack_tags=base.get("basic_attack_tags", []),
            thumbnail=base.get("thumbnail"),
            evolution=evolution,
            abilities=abilities,
            passives=passives,
        )


@dataclass
class Material:
    id: str
    name: str
    obtain_method: str
    image: str | None = None

    @classmethod
    def from_raw(cls, material_id: str, raw: dict) -> "Material":
        return cls(
            id=material_id,
            name=raw.get("name", material_id),
            obtain_method=raw.get("obtain_method", ""),
            image=raw.get("image"),
        )


@dataclass
class Currency:
    id: str
    name: str
    obtain_methods: list[str]
    used_for: list[str]
    image: str | None = None

    @classmethod
    def from_raw(cls, currency_id: str, raw: dict) -> "Currency":
        return cls(
            id=currency_id,
            name=raw.get("name", currency_id),
            obtain_methods=raw.get("obtain_methods", []),
            used_for=raw.get("used_for", []),
            image=raw.get("image"),
        )


@dataclass
class StatusEffect:
    id: str
    name: str
    description: str
    type: str

    @classmethod
    def from_raw(cls, effect_id: str, raw: dict) -> "StatusEffect":
        return cls(
            id=effect_id,
            name=raw.get("name", effect_id),
            description=raw.get("description", ""),
            type=raw.get("type", ""),
        )


@dataclass
class Orb:
    id: str
    name: str
    description: str
    obtain_method: str
    unit_specific: list[str] | None
    granted_ability: Ability | None
    image: str | None = None

    @classmethod
    def from_raw(cls, raw: dict) -> "Orb":
        granted = raw.get("granted_ability")
        return cls(
            id=raw.get("id", ""),
            name=raw.get("name", "Unknown Orb"),
            description=raw.get("description", ""),
            obtain_method=raw.get("obtain_method", ""),
            unit_specific=raw.get("unit_specific"),
            granted_ability=Ability.from_raw(granted) if granted else None,
            image=raw.get("image"),
        )