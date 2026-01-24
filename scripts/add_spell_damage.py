#!/usr/bin/env python3
"""
Add damage column to spells.csv by extracting damage dice from descriptions.

Uses calculate_average_damage from parsers.py to compute average damage.

Usage:
    python scripts/add_spell_damage.py
"""

import re
import sys
import pandas as pd
from pathlib import Path

# Add notebooks to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'notebooks'))
from helper_files.parsers import calculate_average_damage


def extract_spell_damage(description, level_scaling=None):
    """
    Extract damage dice from a spell description.

    Returns:
        tuple: (base_damage_dice, damage_type, avg_damage)
    """
    if pd.isna(description):
        return '', '', 0

    desc = str(description)

    # Common damage patterns in spell descriptions:
    # "8d6 fire damage"
    # "takes 2d10 radiant damage"
    # "dealing 1d8 thunder damage"
    # "suffers 3d6 necrotic damage"

    # Pattern to find damage dice followed by damage type
    damage_pattern = r'(\d+d\d+(?:\s*\+\s*\d+)?)\s+(\w+)\s+damage'

    matches = re.findall(damage_pattern, desc.lower())

    if not matches:
        # Try alternate patterns
        # "damage equal to 2d8"
        alt_pattern = r'damage\s+(?:equal\s+to\s+)?(\d+d\d+(?:\s*\+\s*\d+)?)'
        alt_matches = re.findall(alt_pattern, desc.lower())
        if alt_matches:
            matches = [(alt_matches[0], 'unspecified')]

    if not matches:
        # Try just finding dice notation followed by "damage"
        simple_pattern = r'(\d+d\d+).*?damage'
        simple_matches = re.findall(simple_pattern, desc.lower())
        if simple_matches:
            matches = [(simple_matches[0], 'unspecified')]

    if matches:
        # Take the first (primary) damage
        damage_dice, damage_type = matches[0]
        avg_damage = calculate_average_damage(damage_dice)
        return damage_dice, damage_type, avg_damage

    return '', '', 0


def extract_all_damage_instances(description):
    """
    Extract ALL damage dice instances from a spell description.
    Useful for spells that deal multiple types of damage.

    Returns:
        list of tuples: [(dice, type, avg), ...]
    """
    if pd.isna(description):
        return []

    desc = str(description)
    damage_pattern = r'(\d+d\d+(?:\s*\+\s*\d+)?)\s+(\w+)\s+damage'
    matches = re.findall(damage_pattern, desc.lower())

    results = []
    for dice, dtype in matches:
        avg = calculate_average_damage(dice)
        results.append((dice, dtype, avg))

    return results


def main():
    """Add damage columns to spells.csv."""
    # Load spells
    spells_path = Path(__file__).parent.parent / 'data' / 'spells.csv'
    df = pd.read_csv(spells_path)
    print(f"Loaded {len(df)} spells")

    # Extract damage for each spell
    damage_data = df['description'].apply(extract_spell_damage)

    df['damage_dice'] = damage_data.apply(lambda x: x[0])
    df['damage_type'] = damage_data.apply(lambda x: x[1])
    df['avg_damage'] = damage_data.apply(lambda x: x[2])

    # Summary stats
    has_damage = df[df['avg_damage'] > 0]
    print(f"\nSpells with damage: {len(has_damage)} ({len(has_damage)/len(df)*100:.1f}%)")

    # Show breakdown by damage type
    print("\nDamage types:")
    type_counts = has_damage['damage_type'].value_counts()
    for dtype, count in type_counts.head(10).items():
        print(f"  {dtype}: {count}")

    # Show some examples
    print("\nExample damage spells:")
    examples = ['Fireball', 'Magic Missile', 'Eldritch Blast', 'Lightning Bolt', 'Cure Wounds']
    for spell_name in examples:
        spell = df[df['spell_name'] == spell_name]
        if len(spell) > 0:
            row = spell.iloc[0]
            if row['avg_damage'] > 0:
                print(f"  {row['spell_name']}: {row['damage_dice']} {row['damage_type']} (avg: {row['avg_damage']:.1f})")
            else:
                print(f"  {row['spell_name']}: no damage found")

    # Save updated CSV
    df.to_csv(spells_path, index=False)
    print(f"\nSaved updated spells to {spells_path}")

    # Also show highest damage spells
    print("\nTop 10 highest average damage spells:")
    top_damage = df.nlargest(10, 'avg_damage')[['spell_name', 'level', 'damage_dice', 'damage_type', 'avg_damage']]
    print(top_damage.to_string(index=False))


if __name__ == '__main__':
    main()
