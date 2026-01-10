#!/usr/bin/env python3
"""
Create manual train/test split based on creature families.

Strategy:
- Simple creatures (beasts, humanoids, goblins, giants, simple fliers) → ALL TRAINING
- Complex creatures (dragons, demons, devils, angels, elementals) → SPLIT EVENLY
"""

import pandas as pd
import pickle

# Define manual split lists
TRAIN_CREATURES = [
    # Simple creatures - ALL TO TRAINING
    # This will be done by family matching

    # Dragons - SPLIT EVENLY (TRAIN)
    "Young Brass Dragon", "Young Copper Dragon", "Young Bronze Dragon", "Young Blue Dragon", "Young Red Dragon",
    "Adult Brass Dragon", "Adult Black Dragon", "Adult Green Dragon", "Adult Blue Dragon", "Adult Red Dragon",
    "Ancient Brass Dragon", "Ancient Copper Dragon", "Ancient Bronze Dragon", "Ancient Silver Dragon", "Ancient Red Dragon",

    # Demons - SPLIT EVENLY (TRAIN)
    "Vrock", "Glabrezu", "Marilith",

    # Devils - SPLIT EVENLY (TRAIN)
    "Bearded Devil", "Chain Devil", "Horned Devil", "Ice Devil",

    # Angels - SPLIT EVENLY (TRAIN)
    "Deva", "Solar",

    # Elementals - SPLIT EVENLY (TRAIN)
    "Fire Elemental", "Air Elemental",
]

TEST_CREATURES = [
    # Dragons - SPLIT EVENLY (TEST)
    "Young White Dragon", "Young Black Dragon", "Young Green Dragon", "Young Silver Dragon", "Young Gold Dragon",
    "Adult White Dragon", "Adult Copper Dragon", "Adult Bronze Dragon", "Adult Silver Dragon", "Adult Gold Dragon",
    "Ancient White Dragon", "Ancient Black Dragon", "Ancient Green Dragon", "Ancient Blue Dragon", "Ancient Gold Dragon",

    # Demons - SPLIT EVENLY (TEST)
    "Hezrou", "Nalfeshnee", "Balor",

    # Devils - SPLIT EVENLY (TEST)
    "Barbed Devil", "Bone Devil", "Erinyes", "Pit Fiend",

    # Angels - SPLIT EVENLY (TEST)
    "Planetar",

    # Elementals - SPLIT EVENLY (TEST)
    "Earth Elemental", "Water Elemental",
]

# Families that should ALL go to training
TRAIN_FAMILIES = [
    'beast', 'humanoid_simple', 'goblinoid', 'simple_flier',
    'giant_cloud', 'giant_fire', 'giant_frost', 'giant_hill',
    'giant_stone', 'giant_storm', 'giant_other'
]

def extract_family(name):
    """Extract creature family from name."""
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

def create_manual_split_indices(df):
    """
    Create train/test split indices based on manual strategy.

    Returns:
        train_indices, test_indices
    """
    df['family'] = df['Name'].apply(extract_family)

    train_mask = pd.Series([False] * len(df), index=df.index)
    test_mask = pd.Series([False] * len(df), index=df.index)

    # 1. Add all simple families to training
    for family in TRAIN_FAMILIES:
        family_mask = df['family'] == family
        train_mask |= family_mask

    # 2. Add manually specified TRAIN creatures
    for creature_name in TRAIN_CREATURES:
        creature_mask = df['Name'] == creature_name
        if creature_mask.any():
            train_mask |= creature_mask

    # 3. Add manually specified TEST creatures
    for creature_name in TEST_CREATURES:
        creature_mask = df['Name'] == creature_name
        if creature_mask.any():
            test_mask |= creature_mask

    # 4. Everything else goes to training (default)
    remaining_mask = ~(train_mask | test_mask)
    train_mask |= remaining_mask

    train_indices = df[train_mask].index.tolist()
    test_indices = df[test_mask].index.tolist()

    return train_indices, test_indices

# Save the split function for use in notebook
split_data = {
    'train_creatures': TRAIN_CREATURES,
    'test_creatures': TEST_CREATURES,
    'train_families': TRAIN_FAMILIES,
    'extract_family_func': extract_family,
    'create_split_func': create_manual_split_indices
}

with open('data/manual_split_strategy.pkl', 'wb') as f:
    pickle.dump(split_data, f)

print("✅ Manual split strategy saved to: data/manual_split_strategy.pkl")
print(f"\nTrain creatures (manual): {len(TRAIN_CREATURES)}")
print(f"Test creatures (manual): {len(TEST_CREATURES)}")
print(f"Train families (all creatures): {len(TRAIN_FAMILIES)}")
