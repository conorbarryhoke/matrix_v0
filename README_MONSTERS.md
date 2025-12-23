# D&D 5E Monster Database

This directory contains a comprehensive database of D&D 5th Edition monsters from the 2014 Free Basic Rules.

## Files

### Data Files
- **[dnd5e_monsters_2014.csv](dnd5e_monsters_2014.csv)** - Main output file containing 324 monsters with 43 attributes each
- **[monsters_data.json](monsters_data.json)** - Source data downloaded from Roll20 API

### Scripts
- **[parse_monsters.py](parse_monsters.py)** - Python script to parse JSON and generate CSV

## CSV Structure

The CSV file contains the following columns:

### Basic Stats
- Name, Size, Type, Alignment
- AC (Armor Class)
- HP (Hit Points)
- Speed
- Challenge_Rating, XP

### Ability Scores
- STR, STR_Mod, DEX, DEX_Mod, CON, CON_Mod
- INT, INT_Mod, WIS, WIS_Mod, CHA, CHA_Mod

### Skills & Saves
- Saving_Throws
- Skills
- Passive_Perception
- Senses
- Languages

### Defensive Attributes
- Vulnerabilities
- Damage_Vulnerabilities
- Resistances
- Immunities
- Condition_Immunities

### Environment
- Habitat
- Treasure
- Gear

### Abilities
- Traits
- Actions
- Reactions
- Bonus_Actions
- Legendary_Actions
- Legendary_Actions_Num
- Legendary_Actions_Desc

### Source Metadata
- Source_Name
- Image_URL

## Usage Examples

### Find a specific monster
```bash
grep "Goblin" dnd5e_monsters_2014.csv
```

### Count monsters by type
```bash
cut -d',' -f3 dnd5e_monsters_2014.csv | sort | uniq -c | sort -rn
```

### Open in spreadsheet software
Simply open `dnd5e_monsters_2014.csv` in Excel, Google Sheets, or LibreOffice Calc.

## Quick Facts

- **Total Monsters**: 324
- **Source**: D&D 5E Free Basic Rules (2014)
- **Data Provider**: Roll20 Compendium
- **File Size**: ~329KB

## Example Entry

**Goblin**
- AC: 15 (Leather Armor, Shield)
- HP: 7 (2d6)
- CR: 1/4
- Type: humanoid (goblinoid)

**Aboleth**
- AC: 17 (Natural Armor)
- HP: 135 (18d10+36)
- CR: 10
- Type: aberration

## Regenerating the Data

If you need to regenerate the CSV from the JSON source:

```bash
python3 parse_monsters.py
```

This will create a fresh `dnd5e_monsters_2014.csv` file.

## Notes

- Empty values are represented as blank cells (the "—" marker from the source is converted to empty strings)
- Complex abilities (Traits, Actions, etc.) are formatted as "Name: Description | Name: Description" for readability
- All 324 monsters from the 2014 Free Basic Rules are included
- The 2024 ruleset monsters are excluded (they use expansion ID 33335)
