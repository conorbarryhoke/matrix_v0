#!/usr/bin/env python3
"""
Test script to verify the feature_exploration notebook data loading works correctly.
"""

import pandas as pd
import os

print("="*80)
print("Testing Feature Exploration Data Loading")
print("="*80)

# Load raw monster data
print("\n1. Loading raw monster data...")
df_raw = pd.read_csv('data/dnd5e_monsters_from_json.csv')
print(f"   ✅ Loaded {len(df_raw)} creatures from dnd5e_monsters_from_json.csv")
print(f"   Sample columns: {list(df_raw.columns)[:10]}")

# Load engineered features
print("\n2. Loading engineered features...")
df_engineered = pd.read_csv('data/engineered_features.csv')
print(f"   ✅ Loaded {len(df_engineered)} creatures from engineered_features.csv")
print(f"   Sample columns: {list(df_engineered.columns)[:10]}")

# Merge
print("\n3. Merging datasets...")
df = df_raw.merge(df_engineered, on='Name', how='inner', suffixes=('', '_eng'))
print(f"   ✅ Merged dataset has {len(df)} creatures")

# Handle duplicates
duplicate_cols = ['Type_eng', 'Size_eng', 'Challenge_Rating_eng']
df = df.drop(columns=[col for col in duplicate_cols if col in df.columns], errors='ignore')

# Create alias: Special_Abilities is the same as Traits in this dataset
df['Special_Abilities'] = df['Traits']

# Verify required columns
print("\n4. Verifying required columns...")

required_raw = ['Name', 'Special_Abilities', 'Actions', 'Traits', 'Legendary_Actions', 'STR', 'INT', 'WIS']
required_stats = ['HP', 'AC', 'Speed', 'Type']
required_eng = ['cr_numeric', 'estimated_dpr']

all_good = True

for col in required_raw:
    if col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   ✅ {col:<25} present ({non_null}/{len(df)} non-null)")
    else:
        print(f"   ❌ {col:<25} MISSING")
        all_good = False

for col in required_stats:
    if col in df.columns:
        print(f"   ✅ {col:<25} present")
    else:
        print(f"   ❌ {col:<25} MISSING")
        all_good = False

for col in required_eng:
    if col in df.columns:
        print(f"   ✅ {col:<25} present")
    else:
        print(f"   ⚠️  {col:<25} missing (will use fallback)")

# Test family detection
print("\n5. Testing creature family detection...")
from collections import defaultdict

families = defaultdict(list)
modifiers = [
    'greater', 'lesser', 'dire', 'elder', 'young', 'ancient', 'adult',
    'captain', 'warlord', 'lord', 'king', 'queen', 'chief', 'boss'
]

for idx, row in df.iterrows():
    name = row['Name'].lower()
    cr = row['cr_numeric']

    # Extract base name
    base_name = name
    for mod in modifiers:
        base_name = base_name.replace(mod, '').strip()

    families[base_name].append({
        'name': row['Name'],
        'cr': cr,
        'index': idx
    })

# Filter to families with 2+ members
multi_member_families = {k: v for k, v in families.items() if len(v) >= 2}
print(f"   ✅ Found {len(multi_member_families)} creature families with 2+ members")

# Show examples
print("\n   Example families:")
for i, (family_name, members) in enumerate(list(multi_member_families.items())[:5]):
    print(f"   - {family_name.title()}: {len(members)} members")
    for m in sorted(members, key=lambda x: x['cr']):
        print(f"     CR {m['cr']:>4}: {m['name']}")

# Test multiattack parsing
print("\n6. Testing multiattack parsing...")
import re

def count_multiattacks(actions_str):
    if pd.isna(actions_str):
        return 0

    text = str(actions_str).lower()
    if 'multiattack' not in text:
        return 0

    number_words = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8
    }

    patterns = [r'makes (\\w+) attacks', r'(\\w+) attacks']

    max_count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match.isdigit():
                max_count = max(max_count, int(match))
            elif match in number_words:
                max_count = max(max_count, number_words[match])

    return max_count

df['multiattack_count'] = df['Actions'].apply(count_multiattacks)
has_multiattack = (df['multiattack_count'] > 0).sum()
print(f"   ✅ Found {has_multiattack} creatures with multiattack")
print(f"   Max attacks: {df['multiattack_count'].max()}")

# Test spellcaster detection
print("\n7. Testing spellcaster detection...")
df['has_spellcasting'] = df['Special_Abilities'].str.contains('spellcasting', case=False, na=False)
has_spellcasting = df['has_spellcasting'].sum()
print(f"   ✅ Found {has_spellcasting} creatures with spellcasting")

# Test legendary actions
print("\n8. Testing legendary actions detection...")
df['has_legendary_actions'] = df['Legendary_Actions'].notna() & (df['Legendary_Actions'].str.strip() != '')
has_legendary = df['has_legendary_actions'].sum()
print(f"   ✅ Found {has_legendary} creatures with legendary actions")

# Summary
print("\n" + "="*80)
if all_good:
    print("✅ ALL CHECKS PASSED")
    print(f"   Dataset ready with {len(df)} creatures")
    print(f"   Ready for archetype detection!")
else:
    print("⚠️  SOME CHECKS FAILED")
    print("   Review missing columns above")
print("="*80)
