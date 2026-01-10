#!/usr/bin/env python3
"""
Analyze creature families and complexity to help create manual train/test split.
"""

import pandas as pd
import re

# Load the engineered features
df = pd.read_csv('data/engineered_features.csv')

# Parse CR
def parse_cr(cr_str):
    if pd.isna(cr_str):
        return 0
    cr_str = str(cr_str).strip()
    if '/' in cr_str:
        num, denom = cr_str.split('/')
        return float(num) / float(denom)
    try:
        return float(cr_str)
    except:
        return 0

df['cr_numeric'] = df['Challenge_Rating'].apply(parse_cr)

# Calculate feature complexity score
# Count Phase 3 features that are non-zero
phase3_feature_cols = [
    'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb',
    'save_proficiency_count', 'skill_proficiency_count',
    'vulnerability_count', 'condition_immunity_count',
    'has_darkvision', 'has_blindsight', 'has_truesight', 'has_tremorsense',
    'reaction_count', 'bonus_action_count',
    'legendary_action_count', 'has_legendary_actions',
    'has_legendary_resistance', 'has_magic_resistance', 'has_regeneration',
    'has_spellcasting',
    'inflicts_poisoned', 'inflicts_blinded', 'inflicts_charmed',
    'inflicts_deafened', 'inflicts_frightened', 'inflicts_incapacitated',
    'inflicts_paralyzed', 'inflicts_petrified', 'inflicts_prone',
    'inflicts_restrained', 'inflicts_stunned'
]

# Count non-zero features for each creature
df['feature_complexity'] = 0
for col in phase3_feature_cols:
    if col in df.columns:
        df['feature_complexity'] += (df[col] > 0).astype(int)

# Extract creature family/type from name
def extract_family(name):
    name = str(name).lower()

    # Dragons
    if 'dragon' in name:
        if 'ancient' in name:
            return 'dragon_ancient'
        elif 'adult' in name:
            return 'dragon_adult'
        elif 'young' in name:
            return 'dragon_young'
        elif 'wyrmling' in name:
            return 'dragon_wyrmling'
        else:
            return 'dragon_other'

    # Giants
    if 'giant' in name:
        for giant_type in ['cloud', 'fire', 'frost', 'hill', 'stone', 'storm']:
            if giant_type in name:
                return f'giant_{giant_type}'
        return 'giant_other'

    # Goblins/Goblinoids
    if any(x in name for x in ['goblin', 'hobgoblin', 'bugbear']):
        return 'goblinoid'

    # Elementals
    if 'elemental' in name:
        return 'elemental'

    # Demons
    if 'demon' in name or any(x in name for x in ['balor', 'marilith', 'nalfeshnee', 'vrock', 'hezrou', 'glabrezu']):
        return 'demon'

    # Devils
    if 'devil' in name or any(x in name for x in ['pit fiend', 'erinyes', 'bone devil', 'bearded devil']):
        return 'devil'

    # Undead types
    if any(x in name for x in ['zombie', 'skeleton', 'ghoul', 'wight', 'wraith', 'specter', 'ghost', 'vampire', 'lich']):
        return 'undead'

    # Angels
    if 'angel' in name or 'deva' in name or 'solar' in name or 'planetar' in name:
        return 'angel'

    # Beasts
    if any(x in name for x in ['wolf', 'bear', 'lion', 'tiger', 'eagle', 'hawk', 'spider', 'snake', 'crocodile', 'shark', 'rat', 'bat', 'frog', 'cat', 'dog', 'horse', 'ox', 'goat']):
        return 'beast'

    # Simple humanoids
    if any(x in name for x in ['guard', 'knight', 'noble', 'commoner', 'bandit', 'cultist', 'acolyte', 'priest', 'veteran', 'scout']):
        return 'humanoid_simple'

    # Aarakocra, pegasus, etc
    if any(x in name for x in ['aarakocra', 'pegasus', 'griffon', 'hippogriff']):
        return 'simple_flier'

    return 'other'

df['family'] = df['Name'].apply(extract_family)

# Group by family and show statistics
family_stats = df.groupby('family').agg({
    'Name': 'count',
    'cr_numeric': ['min', 'max', 'mean'],
    'feature_complexity': 'mean'
}).round(2)

family_stats.columns = ['count', 'cr_min', 'cr_max', 'cr_mean', 'avg_complexity']
family_stats = family_stats.sort_values('avg_complexity')

print("=" * 80)
print("CREATURE FAMILIES BY COMPLEXITY")
print("=" * 80)
print("\nSimple creatures (low complexity) should go to TRAINING")
print("Complex creatures (high complexity) should be SPLIT evenly\n")
print(family_stats.to_string())

# Show specific examples for key families
print("\n" + "=" * 80)
print("EXAMPLES OF CREATURES BY FAMILY")
print("=" * 80)

priority_families = [
    'beast', 'humanoid_simple', 'goblinoid', 'simple_flier',  # Simple - mostly train
    'giant_hill', 'giant_stone', 'giant_frost', 'giant_fire', 'giant_cloud', 'giant_storm',  # Giants
    'dragon_wyrmling', 'dragon_young', 'dragon_adult', 'dragon_ancient',  # Dragons by age
    'demon', 'devil', 'angel', 'undead', 'elemental'  # Other complex
]

for family in priority_families:
    creatures = df[df['family'] == family][['Name', 'cr_numeric', 'feature_complexity']].sort_values('cr_numeric')
    if len(creatures) > 0:
        print(f"\n{family.upper()} (n={len(creatures)}, avg_complexity={creatures['feature_complexity'].mean():.1f}):")
        print(creatures.to_string(index=False))

# Generate suggested split strategy
print("\n" + "=" * 80)
print("SUGGESTED SPLIT STRATEGY")
print("=" * 80)

print("\n1. ALL TO TRAINING (simple creatures with minimal features):")
for family in ['beast', 'humanoid_simple', 'goblinoid', 'simple_flier']:
    count = len(df[df['family'] == family])
    if count > 0:
        print(f"   - {family}: {count} creatures")

print("\n2. ALL TO TRAINING (all giants - consistent simple pattern):")
giant_families = [f for f in df['family'].unique() if f.startswith('giant_')]
for family in sorted(giant_families):
    count = len(df[df['family'] == family])
    if count > 0:
        print(f"   - {family}: {count} creatures")

print("\n3. SPLIT EVENLY (complex creatures with many features):")
for family in ['dragon_young', 'dragon_adult', 'dragon_ancient', 'demon', 'devil', 'angel']:
    creatures_list = df[df['family'] == family]['Name'].tolist()
    if len(creatures_list) > 0:
        print(f"\n   {family} ({len(creatures_list)} creatures):")
        for i, name in enumerate(creatures_list):
            split = "TRAIN" if i % 2 == 0 else "TEST"
            print(f"      {split}: {name}")

# Export full list with suggested split
df_export = df[['Name', 'Type', 'cr_numeric', 'family', 'feature_complexity']].copy()
df_export['suggested_split'] = 'train'  # Default

# Mark complex families for even split
complex_families = ['dragon_young', 'dragon_adult', 'dragon_ancient', 'demon', 'devil', 'angel', 'undead']
for family in complex_families:
    family_creatures = df_export[df_export['family'] == family].index
    for i, idx in enumerate(family_creatures):
        df_export.loc[idx, 'suggested_split'] = 'train' if i % 2 == 0 else 'test'

df_export = df_export.sort_values(['family', 'cr_numeric'])
df_export.to_csv('data/suggested_train_test_split.csv', index=False)

print("\n" + "=" * 80)
print("✅ Full suggested split saved to: data/suggested_train_test_split.csv")
print("=" * 80)

print("\nSummary:")
train_count = len(df_export[df_export['suggested_split'] == 'train'])
test_count = len(df_export[df_export['suggested_split'] == 'test'])
print(f"   Training set: {train_count} creatures ({train_count/len(df_export)*100:.1f}%)")
print(f"   Test set: {test_count} creatures ({test_count/len(df_export)*100:.1f}%)")
