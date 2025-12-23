#!/usr/bin/env python3
"""
D&D 5E Monster Database Parser
Parses Roll20 JSON data and creates a comprehensive CSV file
"""

import json
import csv
import sys


def parse_ability_json(ability_str):
    """Parse JSON string containing abilities (traits, actions, etc.)"""
    if ability_str == "—" or not ability_str:
        return ""

    try:
        abilities = json.loads(ability_str)
        # Format as "Name: Description | Name: Description | ..."
        parts = []
        for ability in abilities:
            name = ability.get('Name', '')
            desc = ability.get('Desc', '')
            if name:
                parts.append(f"{name}: {desc}")
        return " | ".join(parts)
    except json.JSONDecodeError:
        # If not valid JSON, return as-is
        return ability_str
    except Exception as e:
        print(f"Error parsing ability: {e}", file=sys.stderr)
        return ability_str


def clean_value(value):
    """Clean up value for CSV output"""
    if value == "—":
        return ""
    return str(value).strip()


def parse_monsters(json_file, output_csv):
    """Parse monster JSON and create CSV"""

    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse the results array (it's a JSON string)
    results = json.loads(data['results'])

    # Filter for 2014 rules (expansion ID 34047)
    monsters_2014 = [m for m in results if m['a'][1] == 34047]

    print(f"Found {len(monsters_2014)} monsters from 2014 Free Basic Rules")

    # Define CSV columns
    columns = [
        'Name', 'Size', 'Type', 'Alignment',
        'AC', 'HP', 'Speed', 'Challenge_Rating', 'XP',
        'STR', 'STR_Mod', 'DEX', 'DEX_Mod', 'CON', 'CON_Mod',
        'INT', 'INT_Mod', 'WIS', 'WIS_Mod', 'CHA', 'CHA_Mod',
        'Saving_Throws', 'Skills', 'Passive_Perception', 'Senses', 'Languages',
        'Vulnerabilities', 'Damage_Vulnerabilities', 'Resistances',
        'Immunities', 'Condition_Immunities',
        'Habitat', 'Treasure', 'Gear',
        'Traits', 'Actions', 'Reactions', 'Bonus_Actions',
        'Legendary_Actions', 'Legendary_Actions_Num', 'Legendary_Actions_Desc',
        'Source_Name', 'Image_URL'
    ]

    # Open CSV file for writing
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()

        # Process each monster
        for monster in monsters_2014:
            c = monster['c']  # Attribute array
            a = monster['a']  # Metadata array

            # Build row data
            row = {
                'Name': monster['n'],
                'Size': clean_value(c[0]),
                'Type': clean_value(c[1]),
                'Alignment': clean_value(c[2]),
                'HP': clean_value(c[3]),
                'AC': clean_value(c[4]),
                'Speed': clean_value(c[5]),
                'Challenge_Rating': clean_value(c[6]),
                'XP': clean_value(c[7]),
                # Ability scores (indexes 10-21)
                'STR': clean_value(c[10]),
                'STR_Mod': clean_value(c[11]),
                'DEX': clean_value(c[12]),
                'DEX_Mod': clean_value(c[13]),
                'CON': clean_value(c[14]),
                'CON_Mod': clean_value(c[15]),
                'INT': clean_value(c[16]),
                'INT_Mod': clean_value(c[17]),
                'WIS': clean_value(c[18]),
                'WIS_Mod': clean_value(c[19]),
                'CHA': clean_value(c[20]),
                'CHA_Mod': clean_value(c[21]),
                # Skills and saves
                'Saving_Throws': clean_value(c[22]),
                'Skills': clean_value(c[23]),
                'Passive_Perception': clean_value(c[29]),
                'Senses': clean_value(c[30]),
                'Languages': clean_value(c[31]),
                # Defensive attributes
                'Vulnerabilities': clean_value(c[24]),
                'Damage_Vulnerabilities': clean_value(c[25]),
                'Resistances': clean_value(c[26]),
                'Immunities': clean_value(c[27]),
                'Condition_Immunities': clean_value(c[28]),
                # Environment
                'Habitat': clean_value(c[32]),
                'Treasure': clean_value(c[33]),
                'Gear': clean_value(c[34]),
                # Abilities (parse JSON strings)
                'Traits': parse_ability_json(c[35]),
                'Actions': parse_ability_json(c[36]),
                'Reactions': parse_ability_json(c[42]),
                'Bonus_Actions': parse_ability_json(c[43]),
                'Legendary_Actions': parse_ability_json(c[44]),
                'Legendary_Actions_Num': clean_value(c[45]),
                'Legendary_Actions_Desc': clean_value(c[46]),
                # Source metadata
                'Source_Name': a[2],
                'Image_URL': a[3]
            }

            writer.writerow(row)

    print(f"Successfully created {output_csv} with {len(monsters_2014)} monsters")


if __name__ == "__main__":
    json_file = "monsters_data.json"
    output_csv = "dnd5e_monsters_2014.csv"

    try:
        parse_monsters(json_file, output_csv)
        print(f"\nDone! Check {output_csv} for the complete monster database.")
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Please ensure the file exists.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
