{
  "id": "unit_a",
  "name": "Unit A",
  "tags": ["ground", "hybrid"],
  "enchant": "fire",
  "rarity_range": [5, 5],
  "evolution_line": ["unit_a", "unit_a_evolved", "unit_a_ascended"],
  "obtain_method": "Summon Banner",
  "basic_attack_tags": ["bleed"],
  "image": "assets/units/unit_a.png"
}

{
  "requirements": {
    "materials": { "a": 3, "b": 2 },
    "conditions": { "kills": 5000 }
  },
  "image": "assets/evolutions/unit_a_evolved.png"
}

[
  {
    "name": "Burst",
    "description": "Text",
    "cooldown": 20,
    "global_cd": null,
    "tags": ["nuke", "aoe", "burn"],
    "image": "assets/abilities/unit_a_abil.png"
  }
]

[
  {
    "name": "Heat",
    "description": "Text",
    "cooldown": null,
    "global_cd": null,
    "tags": ["self-buff"]
  }
]

{
  "burn": {
    "name": "Burn",
    "description": "Text",
    "type": "damage_over_time"
  }
}

{
  "shard": {
    "name": "Shard",
    "obtain_method": "W1 Trials",
    "image": "assets/materials/shard.png"
  }
}

{
  "codes": [
    { "code": "CODE", "reward": "5000 Gold, 10 Gems" }
  ]
}


{
  "gold": {
    "name": "Gold",
    "obtain_methods": ["Story rewards"],
    "used_for": ["G Banner"],
    "image": "assets/currencies/gold.png"
  }
}

{
  "name": "Cash Boost",
  "description": "Text"
}


{
  "id": "orb_a",
  "name": "Orb",
  "description": "Text",
  "obtain_method": "Raid Rewards",
  "unit_specific": null,
  "granted_ability": null,
  "image": "assets/orbs/orb_a.png"
}

{
  "stages": [
    {
      "id": "w1_story_1",
      "name": "Story 1",
      "description": "The first stage of World 1 story.",
      "rewards": { "currencies": { "gold": 500 }, "materials": { "Unit": 1 } },
      "image": "assets/gamemodes/w1_story_1.png"
    }
  ]
}

{
  "name": "Tournament Mode",
  "description": "",
  "format": "",
  "rules": "",
  "image": "assets/gamemodes/tournament.png"
}