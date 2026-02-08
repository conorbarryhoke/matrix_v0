"""
Parsing functions for the HP prediction model.

This module contains all functions that parse raw creature data
(strings, JSON) into numeric features for the model.
"""

import re
import json
import pandas as pd

from .feature_config import (
    EXPECTED_COMBAT_ROUNDS,
    DMG_AC_ADJUSTMENTS,
    DMG_ATTACK_ADJUSTMENTS,
    DMG_DPR_ADJUSTMENTS,
    DMG_HP_PER_USE,
    DMG_HP_BY_TIER,
    DMG_HP_PERCENTAGE,
    DMG_HP_MULTIPLIER,
    DMG_FEATURE_NAMES,
    get_cr_tier,
)


# =============================================================================
# BASIC PARSERS
# =============================================================================

def parse_cr(cr_str):
    """Parse CR string (e.g., '1/4', '3') to numeric value."""
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


def parse_hp(hp_str):
    """Parse HP string (e.g., '45 (6d10 + 12)') to average HP."""
    if pd.isna(hp_str):
        return 0
    hp_str = str(hp_str).strip()
    match = re.match(r'(\d+)', hp_str)
    return int(match.group(1)) if match else 0


def parse_hp_avg(hp_str):
    """Parse HP from Lazy 5e format (e.g., '65 (49-81)') to average."""
    if pd.isna(hp_str):
        return 0
    match = re.match(r'(\d+)', str(hp_str))
    return int(match.group(1)) if match else 0

def adjust_hp_baseline(row):
    """Adjust HP baselines: +50% for CR <= 1, +20% for CR >= 2"""
    if row['cr_numeric'] <= 1.0:
        return row['hp_baseline'] * 1.5
    else:
        return row['hp_baseline'] * 1.2

def parse_bonus(bonus_str):
    """Parse attack bonus - handles both numeric (3) and '+3' format."""
    if pd.isna(bonus_str):
        return 0
    bonus_str = str(bonus_str).strip()
    # Try to match "+3" format first
    match = re.search(r'\+(\d+)', bonus_str)
    if match:
        return int(match.group(1))
    # Try direct numeric format
    try:
        return int(bonus_str)
    except:
        return 0


def parse_ac(ac_str):
    """Parse AC string (e.g., '15 (natural armor)') to numeric."""
    if pd.isna(ac_str):
        return 10
    match = re.search(r'\d+', str(ac_str))
    return int(match.group()) if match else 10


# =============================================================================
# SPEED PARSERS
# =============================================================================

def parse_speed(speed_str, speed_type):
    """
    Parse speed string for a specific movement type.

    Args:
        speed_str: Speed string like "30 ft., fly 60 ft., swim 30 ft."
        speed_type: One of 'ground', 'fly', 'swim', 'burrow', 'climb'

    Returns:
        Speed in feet (int)
    """
    if pd.isna(speed_str):
        return 0
    speed_str = str(speed_str).lower()
    if speed_type == 'ground':
        match = re.search(r'^(\d+)\s*ft', speed_str)
        return int(match.group(1)) if match else 0
    else:
        pattern = rf'{speed_type}\s+(\d+)\s*ft'
        match = re.search(pattern, speed_str)
        return int(match.group(1)) if match else 0


# Size ordinal mapping
SIZE_ORDINAL_MAP = {
    'Tiny': 0, 'Small': 1, 'Medium': 2, 'Large': 3, 'Huge': 4, 'Gargantuan': 5
}


def parse_size_ordinal(size_str):
    """Parse size string to ordinal value."""
    return SIZE_ORDINAL_MAP.get(size_str, 2)  # Default to Medium


# =============================================================================
# PROFICIENCY PARSERS
# =============================================================================

def count_proficiencies(prof_str):
    """Count comma-separated proficiencies, handling empty/dash values."""
    if pd.isna(prof_str) or str(prof_str).strip() == '' or str(prof_str).strip() == '—':
        return 0
    return len([x.strip() for x in str(prof_str).split(',') if x.strip() and x.strip() != '—'])


# =============================================================================
# SENSE PARSERS
# =============================================================================

def has_sense(sense_str, sense_type):
    """Check if creature has a specific sense type."""
    if pd.isna(sense_str):
        return 0
    return 1 if sense_type in str(sense_str).lower() else 0


def parse_sense_range(sense_str, sense_type):
    """Parse range of a specific sense in feet."""
    if pd.isna(sense_str):
        return 0
    pattern = rf'{sense_type}\s+(\d+)\s*ft'
    match = re.search(pattern, str(sense_str).lower())
    return int(match.group(1)) if match else 0


def parse_passive_perception(sense_str):
    """Parse passive perception from senses string."""
    if pd.isna(sense_str):
        return 10
    match = re.search(r'passive\s+perception\s+(\d+)', str(sense_str).lower())
    return int(match.group(1)) if match else 10


# =============================================================================
# ABILITY COUNT PARSERS
# =============================================================================

def count_abilities(abilities_str):
    """Count the number of abilities in a JSON array string."""
    if pd.isna(abilities_str) or str(abilities_str).strip() == '' or str(abilities_str).strip() == '—':
        return 0
    try:
        abilities = json.loads(abilities_str)
        return len(abilities)
    except (json.JSONDecodeError, TypeError):
        return 0


def parse_legendary_actions(leg_str):
    """
    Parse legendary actions.

    Returns:
        tuple: (has_legendary, action_count, actions_per_round)
    """
    if pd.isna(leg_str) or str(leg_str).strip() == '' or str(leg_str).strip() == '—':
        return 0, 0, 0
    text = str(leg_str).lower()
    has_leg = 1
    count_match = re.search(r'(\d+)\s+legendary\s+actions?', text)
    per_round = int(count_match.group(1)) if count_match else 3
    action_count = len([x for x in re.split(r'\n+|\*\s+', text) if x.strip() and 'can take' not in x.lower()])
    return has_leg, action_count, per_round


# =============================================================================
# COMBAT STAT PARSERS
# =============================================================================

def parse_attack_bonus(actions_str):
    """Parse highest attack bonus from JSON-formatted actions."""
    if pd.isna(actions_str):
        return 0
    try:
        actions = json.loads(actions_str)
        bonuses = []
        for action in actions:
            if isinstance(action, dict) and 'Hit Bonus' in action:
                try:
                    bonuses.append(int(action['Hit Bonus']))
                except (ValueError, TypeError):
                    pass
        return max(bonuses) if bonuses else 0
    except (json.JSONDecodeError, TypeError):
        return 0


def parse_save_dc(text_str):
    """Parse highest save DC from text (traits, actions, reactions, legendary)."""
    if pd.isna(text_str):
        return 0
    matches = re.findall(r'dc\s+(\d+)', str(text_str).lower())
    return max([int(m) for m in matches]) if matches else 0


def calculate_average_damage(damage_str):
    """
    Calculate average damage from dice notation like '2d8 + 5'.

    Returns:
        float: Expected average damage
    """
    if not damage_str:
        return 0

    total = 0
    # Match patterns like "2d8 + 5" or "1d10+3"
    patterns = re.findall(r'(\d+)d(\d+)(?:\s*[+\-]\s*(\d+))?', str(damage_str))

    for match in patterns:
        num_dice = int(match[0])
        die_size = int(match[1])
        modifier = int(match[2]) if match[2] else 0
        avg = num_dice * (die_size + 1) / 2 + modifier
        total += avg

    return total


def parse_dpr_from_json(actions_str):
    """
    Parse DPR from JSON action structures.
    Handles multiattack and calculates total DPR.
    Also extracts conditional damage from Desc fields (e.g., poison on failed save).

    Returns:
        float: Estimated damage per round
    """
    if pd.isna(actions_str):
        return 0

    try:
        actions = json.loads(actions_str)
    except (json.JSONDecodeError, TypeError):
        return 0

    # Build a map of attack names to their damage
    attack_damages = {}
    multiattack_desc = None

    for action in actions:
        if not isinstance(action, dict):
            continue

        name = action.get('Name', '').lower()

        if name == 'multiattack':
            multiattack_desc = action.get('Desc', '').lower()
        elif 'Damage' in action:
            # Calculate base damage
            damage = calculate_average_damage(action.get('Damage', ''))

            # Add secondary damage if present in Damage 2 field
            if 'Damage 2' in action:
                damage += calculate_average_damage(action.get('Damage 2', ''))

            # Check Desc field for additional conditional damage
            desc = action.get('Desc', '')
            if desc:
                desc_lower = desc.lower()
                # Look for patterns like "taking 22 (4d10) poison damage"
                conditional_patterns = [
                    r'taking\s+(\d+)\s*\(([^)]+)\)\s*(?:\w+\s+)?damage',
                    r'takes\s+(\d+)\s*\(([^)]+)\)\s*(?:\w+\s+)?damage',
                    r'plus\s+(\d+)\s*\(([^)]+)\)\s*(?:\w+\s+)?damage',
                    r'and\s+(\d+)\s*\(([^)]+)\)\s*(?:\w+\s+)?damage',
                ]

                for pattern in conditional_patterns:
                    matches = re.findall(pattern, desc_lower)
                    for match in matches:
                        conditional_dmg = calculate_average_damage(match[1])

                        # Check if there's a saving throw - apply 50% modifier
                        if 'saving throw' in desc_lower or 'save' in desc_lower:
                            conditional_dmg *= 0.5

                        damage += conditional_dmg

            attack_damages[name] = damage

    # If no attacks found, return 0
    if not attack_damages:
        return 0

    # If no multiattack, return highest single attack damage
    if not multiattack_desc:
        return max(attack_damages.values())

    # Parse multiattack description to determine attack counts
    total_dpr = 0
    attacks_counted = {}

    # Try to match specific attacks mentioned in multiattack
    for attack_name, damage in attack_damages.items():
        patterns = [
            rf'(\w+)\s+{re.escape(attack_name)}s?\s+attacks?',
            rf'(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}s?',
            rf'makes?\s+(\w+)\s+{re.escape(attack_name)}s?\s+attacks?',
            rf'makes?\s+(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}s?',
            rf'(\w+)\s+with\s+(?:its\s+)?{re.escape(attack_name)}s?',
        ]

        for pattern in patterns:
            match = re.search(pattern, multiattack_desc)
            if match:
                count_word = match.group(1).lower()
                number_map = {
                    'one': 1, 'a': 1, 'an': 1, 'two': 2, 'three': 3,
                    'four': 4, 'five': 5, 'six': 6
                }
                count = number_map.get(count_word, 0)
                if count == 0:
                    try:
                        count = int(count_word)
                    except ValueError:
                        count = 0

                if count > 0:
                    total_dpr += count * damage
                    attacks_counted[attack_name] = count
                    break

    # If we found specific attacks, check for remaining attacks to fill
    if total_dpr > 0:
        total_attack_match = re.search(r'makes?\s+(\w+)\s+attacks?', multiattack_desc)
        if total_attack_match:
            total_word = total_attack_match.group(1).lower()
            number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
            total_attacks = number_map.get(total_word, 0)

            counted_attacks = sum(attacks_counted.values())
            remaining_attacks = total_attacks - counted_attacks

            if remaining_attacks > 0:
                remaining_options = {k: v for k, v in attack_damages.items() if k not in attacks_counted}
                if remaining_options:
                    best_remaining = max(remaining_options.values())
                    total_dpr += remaining_attacks * best_remaining

        return total_dpr

    # FALLBACK: If no specific attacks matched, use generic count with highest damage
    match = re.search(r'makes?\s+(\w+)\s+attacks?', multiattack_desc)
    if match:
        count_word = match.group(1).lower()
        number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
        count = number_map.get(count_word, 2)
        total_dpr = count * max(attack_damages.values())
    else:
        total_dpr = 2 * max(attack_damages.values())

    return total_dpr


def parse_charge_bonus_attack(traits_str, actions_str):
    """
    Parse burst DPR from conditional one-round damage traits.
    Returns additional DPR amortized over EXPECTED_COMBAT_ROUNDS.

    Handles:
    - Charge / Trampling Charge: bonus attack on charge hit
    - Pounce: bonus attack on pounce hit
    - Surprise Attack: extra damage on first round
    - Dive Attack: extra damage on dive
    - Wounded Fury: extra damage when wounded
    - Death Burst: on-death AoE damage × 2 targets (per DMG)
    - Swallow: ongoing acid damage (2 rounds per DMG)

    NOTE: Rampage is NOT here — it uses fixed +2 DPR via DMG_DPR_ADJUSTMENTS.
    """
    if pd.isna(traits_str) or pd.isna(actions_str):
        return 0

    try:
        traits = json.loads(traits_str)
        actions = json.loads(actions_str)
    except (json.JSONDecodeError, TypeError):
        return 0

    # Build attack damage map from actions
    attack_damages = {}
    for action in actions:
        if not isinstance(action, dict):
            continue
        name = action.get('Name', '').lower()
        if 'Damage' in action:
            damage = calculate_average_damage(action.get('Damage', ''))
            if 'Damage 2' in action:
                damage += calculate_average_damage(action.get('Damage 2', ''))
            attack_damages[name] = damage

    bonus_dpr = 0

    for trait in traits:
        if not isinstance(trait, dict):
            continue

        trait_name = trait.get('Name', '').lower()
        trait_desc = trait.get('Desc', '').lower()

        # Charge / Pounce: bonus attack from the trait
        if any(x in trait_name for x in ['charge', 'pounce']):
            match = re.search(r'can make (?:one|an?|another) (\w+) attack', trait_desc)
            if not match:
                match = re.search(r'can make (?:one|an?|another) attack with (?:its )?(\w+)', trait_desc)
            if match:
                attack_name = match.group(1).lower()
                for action_name, damage in attack_damages.items():
                    if attack_name in action_name:
                        bonus_dpr += damage * (1 / EXPECTED_COMBAT_ROUNDS)
                        break

        # Surprise Attack: "extra X (YdZ) damage" on first round
        elif 'surprise attack' in trait_name:
            match = re.search(r'extra\s+(\d+)\s*\(\d+d\d+\)\s*damage', trait_desc)
            if match:
                bonus_dpr += int(match.group(1)) * (1 / EXPECTED_COMBAT_ROUNDS)

        # Dive Attack: "extra X (YdZ) damage" on dive
        elif 'dive attack' in trait_name or 'dive' in trait_name:
            match = re.search(r'extra\s+(\d+)\s*\(\d+d\d+\)\s*damage', trait_desc)
            if match:
                bonus_dpr += int(match.group(1)) * (1 / EXPECTED_COMBAT_ROUNDS)

        # Wounded Fury: extra damage when wounded
        elif 'wounded fury' in trait_name:
            match = re.search(r'extra\s+(\d+)\s*\(\d+d\d+\)\s*damage', trait_desc)
            if match:
                bonus_dpr += int(match.group(1)) * (1 / EXPECTED_COMBAT_ROUNDS)

        # Death Burst: on-death AoE, assume 2 creatures hit (per DMG)
        elif 'death burst' in trait_name:
            match = re.search(r'(\d+)\s*\(\d+d\d+\)\s*(?:\w+\s+)?damage', trait_desc)
            if match:
                bonus_dpr += int(match.group(1)) * 2 * (1 / EXPECTED_COMBAT_ROUNDS)

    # Swallow: check actions for swallow with ongoing acid damage
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_name = action.get('Name', '').lower()
        if 'swallow' in action_name:
            action_desc = action.get('Desc', '').lower()
            match = re.search(r'(\d+)\s*\(\d+d\d+\)\s*(?:acid|fire|bludgeoning)?\s*damage\s*at the start', action_desc)
            if match:
                # DMG: "assume 2 rounds of acid damage"
                bonus_dpr += int(match.group(1)) * 2 * (1 / EXPECTED_COMBAT_ROUNDS)

    return bonus_dpr


def parse_legendary_actions_dpr(legendary_str):
    """
    Parse legendary actions to calculate maximum DPR.
    Uses knapsack-style optimization to find damage-maximizing combination.

    Returns:
        float: Max damage per round from legendary actions
    """
    if pd.isna(legendary_str) or str(legendary_str).strip() == '' or str(legendary_str).strip() == '—':
        return 0

    text = str(legendary_str)

    # Determine action budget (default 3)
    budget_match = re.search(r'(\d+)\s+legendary\s+actions?', text.lower())
    action_budget = int(budget_match.group(1)) if budget_match else 3

    # Split into individual legendary actions
    action_blocks = re.split(r'\n\s*\n|\n\*\s*', text)

    legendary_actions = []

    for block in action_blocks:
        if not block.strip():
            continue

        # Skip the preamble text
        if 'can take' in block.lower() or 'only one legendary action' in block.lower():
            continue

        # Parse action cost (default 1)
        cost_match = re.search(r'\(costs?\s+(\d+)\s+actions?\)', block, re.IGNORECASE)
        cost = int(cost_match.group(1)) if cost_match else 1

        # Parse damage from dice notation
        damage = 0
        damage_matches = re.findall(r'(\d+)\s*\((\d+d\d+(?:\s*[+\-]\s*\d+)?)\)', block)
        if damage_matches:
            damage = int(damage_matches[0][0])
        else:
            dice_matches = re.findall(r'(\d+)d(\d+)(?:\s*[+\-]\s*(\d+))?', block)
            if dice_matches:
                for match in dice_matches:
                    num_dice = int(match[0])
                    die_size = int(match[1])
                    modifier = int(match[2]) if match[2] else 0
                    damage += num_dice * (die_size + 1) / 2 + modifier

        if damage > 0:
            legendary_actions.append({
                'cost': cost,
                'damage': damage
            })

    # Knapsack-style optimization
    dp = {0: (0, [])}

    for action in legendary_actions:
        cost = action['cost']
        damage = action['damage']

        new_entries = {}
        for budget_used, (current_damage, actions_used) in dp.items():
            new_budget = budget_used + cost
            if new_budget <= action_budget:
                new_damage = current_damage + damage
                if new_budget not in dp or new_damage > dp[new_budget][0]:
                    new_entries[new_budget] = (new_damage, actions_used + [action])

        dp.update(new_entries)

    # Find the maximum damage achievable within budget
    max_damage = 0
    for budget_used in range(action_budget + 1):
        if budget_used in dp:
            max_damage = max(max_damage, dp[budget_used][0])

    return max_damage


def parse_legendary_conditions(legendary_str):
    """
    Parse legendary actions to extract conditions inflicted.

    Returns:
        list: Conditions that can be inflicted by legendary actions
    """
    if pd.isna(legendary_str) or str(legendary_str).strip() == '' or str(legendary_str).strip() == '—':
        return []

    text = str(legendary_str)
    action_blocks = re.split(r'\n\s*\n|\n\*\s*', text)

    conditions_found = []
    condition_keywords = [
        'poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
        'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned'
    ]

    for block in action_blocks:
        if not block.strip():
            continue
        if 'can take' in block.lower() or 'only one legendary action' in block.lower():
            continue

        for condition in condition_keywords:
            if condition in block.lower():
                conditions_found.append(condition)

    return list(set(conditions_found))


# =============================================================================
# SPECIAL TRAIT PARSERS
# =============================================================================

def extract_spellcaster_level(text):
    """Extract spellcaster level from text."""
    if pd.isna(text):
        return 0
    text = str(text).lower()
    # Match patterns like "9th-level spellcaster"
    match = re.search(r'(\d+)(?:st|nd|rd|th)[-\s]level\s+spellcaster', text)
    if match:
        return int(match.group(1))
    # Also check for "casts spells as a X-level" pattern
    match = re.search(r'casts?\s+spells?\s+as\s+a?\s*(\d+)(?:st|nd|rd|th)[-\s]level', text)
    if match:
        return int(match.group(1))
    return 0


def has_advantage_condition(row):
    """
    Check if creature has abilities granting advantage on attacks.

    Detects:
    - Pack Tactics: advantage when ally adjacent
    - Blood Frenzy: advantage vs bloodied targets
    - Reckless: advantage on melee attacks (with tradeoff)
    - Ambusher/Assassinate: advantage on surprised targets
    - Grappler: advantage vs grappled targets
    """
    advantage_patterns = [
        r'pack tactics',
        r'blood frenzy',
        r'reckless',
        r'ambusher',
        r'assassinate',
        r'grappler',
        r'has advantage on.{0,20}attack roll',
        r'have advantage on.{0,20}attack roll',
        r'advantage on attack rolls against',
    ]

    all_text = ''

    if pd.notna(row.get('Traits')) and row.get('Traits') != '—':
        try:
            traits = json.loads(row['Traits'])
            for trait in traits:
                all_text += ' ' + trait.get('Name', '') + ' ' + trait.get('Desc', '')
        except:
            pass

    if pd.notna(row.get('Actions')) and row.get('Actions') != '—':
        try:
            actions = json.loads(row['Actions'])
            for action in actions:
                all_text += ' ' + action.get('Name', '') + ' ' + action.get('Desc', '')
        except:
            pass

    all_text_lower = all_text.lower()

    for pattern in advantage_patterns:
        if re.search(pattern, all_text_lower):
            return 1

    return 0


def has_disadvantage_condition(row):
    """
    Check if creature has abilities giving it disadvantage on attacks.

    Detects:
    - Sunlight Sensitivity: disadvantage in sunlight
    - Sunlight Weakness: disadvantage in sunlight
    - Light Sensitivity: disadvantage in bright light
    """
    disadvantage_patterns = [
        r'sunlight sensitivity',
        r'sunlight weakness',
        r'light sensitivity',
    ]

    all_text = ''

    if pd.notna(row.get('Traits')) and row.get('Traits') != '—':
        try:
            traits = json.loads(row['Traits'])
            for trait in traits:
                all_text += ' ' + trait.get('Name', '') + ' ' + trait.get('Desc', '')
        except:
            pass

    all_text_lower = all_text.lower()

    for pattern in disadvantage_patterns:
        if re.search(pattern, all_text_lower):
            return 1

    return 0


def has_attackers_advantage(row):
    """
    Check if attackers have advantage against this creature.

    Detects:
    - Reckless: attack rolls against it have advantage
    - Other abilities granting attackers advantage
    """
    vulnerable_patterns = [
        r'attack rolls? against.{0,20}have advantage',
        r'attacks? against.{0,20}has advantage',
        r'reckless',  # Reckless specifically grants attackers advantage
    ]

    all_text = ''

    if pd.notna(row.get('Traits')) and row.get('Traits') != '—':
        try:
            traits = json.loads(row['Traits'])
            for trait in traits:
                all_text += ' ' + trait.get('Name', '') + ' ' + trait.get('Desc', '')
        except:
            pass

    all_text_lower = all_text.lower()

    for pattern in vulnerable_patterns:
        if re.search(pattern, all_text_lower):
            return 1

    return 0


# =============================================================================
# DMG FEATURE DETECTION
# =============================================================================

def _extract_ability_names(row):
    """
    Extract lowercased trait, action, and reaction names from a creature row.

    Returns:
        tuple: (trait_names, action_names, reaction_names, all_names)
    """
    trait_names = []
    action_names = []
    reaction_names = []

    for field, target_list in [('Traits', trait_names), ('Actions', action_names), ('Reactions', reaction_names)]:
        val = row.get(field)
        if pd.notna(val) and str(val).strip() not in ('', '—'):
            try:
                items = json.loads(val)
                for item in items:
                    if isinstance(item, dict):
                        target_list.append(item.get('Name', '').lower())
            except (json.JSONDecodeError, TypeError):
                pass

    return trait_names, action_names, reaction_names, trait_names + action_names + reaction_names


def parse_dmg_features(row):
    """
    Detect all 92 DMG Monster Features from a creature's traits, actions, and reactions.
    Returns a dict of feature_{name}: 0/1 flags for every entry in DMG_FEATURE_NAMES.

    Detection strategy:
    - Default: trait/action/reaction name startswith the feature keyword (snake_case → spaces)
    - Special cases for ~12 features where DMG name ≠ actual trait name in the dataset
    - "Prone" is a synergy detection (inflicts_prone + advantage vs prone targets)
    - "Undead Fortitude" is merged into "relentless"

    claude: See plan file for the full detection strategy table. To add a new feature,
    add it to DMG_FEATURE_NAMES in feature_config.py and add detection logic here
    (either the default startswith will work, or add a special case).
    """
    # Initialize all 92 feature flags to 0
    features = {f'feature_{name}': 0 for name in DMG_FEATURE_NAMES}

    trait_names, action_names, reaction_names, all_names = _extract_ability_names(row)

    # --- Default startswith matching ---
    # Convert snake_case feature names to space-separated keywords for matching.
    # e.g. 'magic_resistance' → 'magic resistance'
    # Skip features that have special-case handling below.
    special_cases = {
        'breath_weapon', 'charge', 'damage_absorption', 'elemental_body',
        'keen_senses', 'relentless', 'shapechange', 'spell_immunity',
        'terrain_camouflage', 'web', 'sure_footed', 'prone', 'invisibility',
        'multiattack',
    }

    for feature_name in DMG_FEATURE_NAMES:
        if feature_name in special_cases:
            continue
        keyword = feature_name.replace('_', ' ')
        for name in all_names:
            if name.startswith(keyword):
                features[f'feature_{feature_name}'] = 1
                break

    # --- Special-case detections ---

    for name in all_names:
        # breath_weapon: actual names are "Fire Breath (Recharge 5-6)", "Acid Breath", etc.
        if 'breath' in name and 'recharge' in name:
            features['feature_breath_weapon'] = 1

        # charge: "Charge" or "Trampling Charge"
        if name.startswith('charge') or name == 'trampling charge':
            features['feature_charge'] = 1

        # damage_absorption: "Lightning Absorption", "Fire Absorption", etc.
        if 'absorption' in name:
            features['feature_damage_absorption'] = 1

        # elemental_body: "Heated Body", "Fire Form", "Water Form", "Air Form"
        if any(kw in name for kw in ['heated body', 'fire form', 'water form', 'air form', 'corrosive form']):
            features['feature_elemental_body'] = 1

        # keen_senses: "Keen Hearing", "Keen Smell", "Keen Hearing and Sight", etc.
        if name.startswith('keen'):
            features['feature_keen_senses'] = 1

        # relentless: "Relentless" or "Undead Fortitude" (merged)
        if name.startswith('relentless') or name.startswith('undead fortitude'):
            features['feature_relentless'] = 1

        # shapechange: "Shapechanger", "Change Shape", "Shapechange"
        if name.startswith('shapechange') or name.startswith('shapechanger') or name.startswith('change shape'):
            features['feature_shapechange'] = 1

        # spell_immunity: "Spell Immunity" or "Limited Magic Immunity"
        if name.startswith('spell immunity') or name.startswith('limited magic immunity'):
            features['feature_spell_immunity'] = 1

        # terrain_camouflage: "Stone Camouflage", "Snow Camouflage", etc. (not "False Appearance")
        if 'camouflage' in name and 'false' not in name:
            features['feature_terrain_camouflage'] = 1

        # sure_footed: may be hyphenated "Sure-Footed"
        if name.startswith('sure-footed') or name.startswith('sure footed'):
            features['feature_sure_footed'] = 1

        # invisibility: "Invisibility" or "Invisible" (but not "Superior Invisibility" — handled by default)
        if name.startswith('invisibility') or name == 'invisible':
            features['feature_invisibility'] = 1

    # web: startswith "web" but NOT "web sense" or "web walker" (those are separate features)
    for name in action_names + trait_names:
        if name.startswith('web') and 'sense' not in name and 'walker' not in name:
            features['feature_web'] = 1
            break

    # multiattack: check Actions only (it's always an action, not a trait)
    for name in action_names:
        if name == 'multiattack':
            features['feature_multiattack'] = 1
            break

    # prone: synergy detection — creature can knock prone AND has advantage vs prone targets
    # This requires inflicts_prone (computed earlier in the pipeline) to be passed in.
    # If inflicts_prone isn't available yet, check trait/action descriptions for prone + advantage.
    inflicts_prone = row.get('inflicts_prone', 0)
    if inflicts_prone == 1:
        # Check if creature has advantage on attacks against prone targets
        all_text = ''
        for field in ['Traits', 'Actions']:
            val = row.get(field)
            if pd.notna(val) and str(val).strip() not in ('', '—'):
                try:
                    items = json.loads(val)
                    for item in items:
                        if isinstance(item, dict):
                            all_text += ' ' + item.get('Desc', '')
                except (json.JSONDecodeError, TypeError):
                    pass
        if re.search(r'advantage on.{0,30}attack roll.{0,30}prone', all_text.lower()):
            features['feature_prone'] = 1

    return features


def _has_ranged_damage(row):
    """Check if a creature can deal damage at range (ranged attacks, breath weapons, or spells)."""
    # Check for ranged weapon/spell attacks in Actions JSON
    actions_str = row.get('Actions')
    if pd.notna(actions_str) and str(actions_str).strip() not in ('', '—'):
        try:
            actions = json.loads(actions_str)
            for action in actions:
                if isinstance(action, dict):
                    action_type = str(action.get('Type', '')).lower()
                    type_attack = str(action.get('Type Attack', '')).lower()
                    if action_type == 'ranged':
                        return True
                    if 'spell attack' in type_attack:
                        return True
        except (json.JSONDecodeError, TypeError):
            pass
    # Check for breath weapon (inherently ranged)
    if row.get('feature_breath_weapon', 0) == 1:
        return True
    # Check for innate spellcasting (typically grants ranged damage)
    if row.get('feature_innate_spellcasting', 0) == 1 or row.get('feature_spellcasting', 0) == 1:
        return True
    return False


def calculate_feature_ac(row):
    """Sum effective AC adjustments from detected DMG features.

    Includes:
    - DMG Monster Features table AC costs (magic resistance +2, etc.)
    - Flying: +2 effective AC if can fly AND deal damage at range AND CR <= 10
    - Saving throws: 3-4 bonuses → +2; 5+ bonuses → +4
    """
    total = 0

    # DMG feature AC adjustments
    for feature_name, ac_bonus in DMG_AC_ADJUSTMENTS.items():
        col = f'feature_{feature_name.replace(" ", "_")}'
        if row.get(col, 0) == 1:
            total += ac_bonus

    # Flying: +2 effective AC if can fly, deal damage at range, and CR <= 10
    cr = row.get('cr_numeric', 0)
    if row.get('has_flying', 0) == 1 and cr <= 10 and _has_ranged_damage(row):
        total += 2

    # Saving throw bonuses: 3-4 → +2, 5+ → +4
    save_count = row.get('save_proficiency_count', 0)
    if save_count >= 5:
        total += 4
    elif save_count >= 3:
        total += 2

    return total


def calculate_feature_attack(row):
    """Sum effective attack bonus adjustments from detected DMG features."""
    total = 0
    for feature_name, attack_bonus in DMG_ATTACK_ADJUSTMENTS.items():
        col = f'feature_{feature_name.replace(" ", "_")}'
        if row.get(col, 0) == 1:
            total += attack_bonus
    return total


def calculate_feature_dpr(row):
    """Sum fixed per-round DPR adjustments from detected DMG features."""
    total = 0
    for feature_name, dpr_bonus in DMG_DPR_ADJUSTMENTS.items():
        col = f'feature_{feature_name}'
        if row.get(col, 0) == 1:
            total += dpr_bonus
    return total


def parse_breath_weapon_dpr(row):
    """
    Calculate DPR contribution from breath weapons.

    Per DMG: "assume the breath weapon hits two targets, and that each target
    fails its saving throw." If the breath weapon DPR (× 2 targets) exceeds
    estimated_dpr, the excess is added as feature_dpr. This avoids double-counting
    since a creature uses breath weapon OR multiattack, not both.
    """
    actions_str = row.get('Actions')
    if pd.isna(actions_str) or str(actions_str).strip() in ('', '—'):
        return 0

    try:
        actions = json.loads(actions_str)
    except (json.JSONDecodeError, TypeError):
        return 0

    best_breath_dpr = 0
    for action in actions:
        if not isinstance(action, dict):
            continue
        name = action.get('Name', '').lower()
        desc = action.get('Desc', '').lower()

        # Match breath weapon actions (e.g., "Fire Breath (Recharge 5-6)")
        if 'breath' not in name:
            continue

        # Parse damage from Desc: "taking 91 (26d6) fire damage"
        match = re.search(r'(\d+)\s*\(\d+d\d+(?:\s*[+\-]\s*\d+)?\)\s*(?:\w+\s+)?damage', desc)
        if match:
            breath_damage = int(match.group(1))
            # DMG: assume 2 targets, each fails save
            breath_total = breath_damage * 2
            best_breath_dpr = max(best_breath_dpr, breath_total)

    if best_breath_dpr <= 0:
        return 0

    # Only add the EXCESS over estimated_dpr (avoids double-counting with multiattack)
    estimated_dpr = row.get('estimated_dpr', 0)
    return max(0, best_breath_dpr - estimated_dpr)


def parse_trait_extra_dpr(row):
    """
    Parse per-round extra damage from traits that add damage on each attack.

    Handles:
    - Sneak Attack: "extra X (YdZ) damage" (once per round)
    - Martial Advantage: "extra X (YdZ) damage" (once per turn)
    - Elemental Body (Heated Body, Fire Form, etc.): reactive damage per hit

    NOTE: Brute, Angelic Weapons, Enlarge say "included in the attack" — their
    damage is already in the action's Damage field and captured by estimated_dpr.
    """
    traits_str = row.get('Traits')
    if pd.isna(traits_str) or str(traits_str).strip() in ('', '—'):
        return 0

    try:
        traits = json.loads(traits_str)
    except (json.JSONDecodeError, TypeError):
        return 0

    extra_dpr = 0

    for trait in traits:
        if not isinstance(trait, dict):
            continue
        trait_name = trait.get('Name', '').lower()
        trait_desc = trait.get('Desc', '').lower()

        # Sneak Attack: "deals an extra X (YdZ) damage"
        if 'sneak attack' in trait_name:
            match = re.search(r'extra\s+(\d+)\s*\(\d+d\d+\)\s*damage', trait_desc)
            if match:
                extra_dpr += int(match.group(1))

        # Martial Advantage: "extra X (YdZ) damage"
        elif 'martial advantage' in trait_name:
            match = re.search(r'extra\s+(\d+)\s*\(\d+d\d+\)\s*damage', trait_desc)
            if match:
                extra_dpr += int(match.group(1))

        # Elemental Body: Heated Body, Fire Form, etc.
        # "takes X (YdZ) fire damage" — reactive damage when touched/hit
        elif any(kw in trait_name for kw in ['heated body', 'fire form', 'water form',
                                              'air form', 'corrosive form']):
            match = re.search(r'(\d+)\s*\(\d+d\d+\)\s*(?:\w+\s+)?damage', trait_desc)
            if match:
                extra_dpr += int(match.group(1))

    return extra_dpr


def calculate_feature_hp(row):
    """
    Calculate effective HP adjustments from DMG features.

    Sums HP bonuses from:
    - Legendary Resistance: per-use HP bonus by CR tier × number of uses
    - Relentless / Undead Fortitude: fixed HP by CR tier
    - Frightful Presence / Horrifying Visage: +25% of hp_baseline (CR ≤ 10 only)
    - Possession / Damage Transfer: multiply effective HP
    - Regeneration: +3 × regen amount per round (per DMG)

    Returns the total HP adjustment to add to hp_baseline.
    """
    cr = row.get('cr_numeric', 0)
    tier = get_cr_tier(cr)
    hp_baseline = row.get('hp_baseline', 0)
    total_hp = 0

    # Per-use HP bonuses (Legendary Resistance)
    for feature_name, tier_values in DMG_HP_PER_USE.items():
        col = f'feature_{feature_name}'
        if row.get(col, 0) != 1:
            continue
        per_use_hp = tier_values.get(tier, 0)
        if per_use_hp <= 0:
            continue
        # Parse number of uses from trait desc (default 3)
        uses = 3
        traits_str = row.get('Traits')
        if pd.notna(traits_str) and str(traits_str).strip() not in ('', '—'):
            try:
                traits = json.loads(traits_str)
                for trait in traits:
                    if isinstance(trait, dict) and feature_name.replace('_', ' ') in trait.get('Name', '').lower():
                        desc = trait.get('Desc', '').lower()
                        match = re.search(r'(\d+)\s*times', desc)
                        if match:
                            uses = int(match.group(1))
                        break
            except (json.JSONDecodeError, TypeError):
                pass
        total_hp += per_use_hp * uses

    # Fixed HP by tier (Relentless)
    for feature_name, tier_values in DMG_HP_BY_TIER.items():
        col = f'feature_{feature_name}'
        if row.get(col, 0) == 1:
            total_hp += tier_values.get(tier, 0)

    # Percentage of hp_baseline (Frightful Presence, Horrifying Visage)
    # DMG: only if "meant to face characters of 10th level or lower" ≈ CR ≤ 10
    for feature_name, pct in DMG_HP_PERCENTAGE.items():
        col = f'feature_{feature_name}'
        if row.get(col, 0) == 1 and cr <= 10:
            total_hp += hp_baseline * pct

    # HP multiplier (Possession, Damage Transfer)
    # feature_hp = hp_baseline × (multiplier - 1) to add the EXTRA, not total
    for feature_name, mult in DMG_HP_MULTIPLIER.items():
        col = f'feature_{feature_name}'
        if row.get(col, 0) == 1:
            total_hp += hp_baseline * (mult - 1)

    # Regeneration: +3 × regen amount per round (per DMG)
    if row.get('feature_regeneration', 0) == 1:
        traits_str = row.get('Traits')
        if pd.notna(traits_str) and str(traits_str).strip() not in ('', '—'):
            try:
                traits = json.loads(traits_str)
                for trait in traits:
                    if isinstance(trait, dict) and 'regeneration' in trait.get('Name', '').lower():
                        desc = trait.get('Desc', '').lower()
                        match = re.search(r'regains\s+(\d+)\s+hit points', desc)
                        if match:
                            total_hp += int(match.group(1)) * 3
                        break
            except (json.JSONDecodeError, TypeError):
                pass

    return total_hp


# =============================================================================
# RESISTANCE/IMMUNITY MULTIPLIERS
# =============================================================================

def get_resistance_multiplier(cr):
    """Get HP penalty multiplier for resistances based on CR."""
    if cr < 1:
        return 0.25
    elif cr <= 4:
        return 0.125
    elif cr <= 10:
        return 0.0625
    elif cr <= 16:
        return 0.0625
    else:  # CR > 16
        return 0.0


def get_immunity_multiplier(cr):
    """Get HP penalty multiplier for immunities based on CR."""
    if cr < 1:
        return 0.25
    elif cr <= 4:
        return 0.25
    elif cr <= 10:
        return 0.25
    elif cr <= 16:
        return 0.125
    else:  # CR > 16
        return 0.0625


# =============================================================================
# FAMILY EXTRACTION
# =============================================================================

def extract_family(name):
    """Extract creature family from name for train/test splitting."""
    name = str(name).lower()

    # Dragon family
    if 'dragon' in name:
        return 'dragon'
    # Giant family
    if 'giant' in name and 'fire' not in name and 'storm' not in name:
        return 'giant'
    # Elemental family
    if any(x in name for x in ['elemental', 'mephit', 'genie', 'djinni', 'efreeti', 'dao', 'marid']):
        return 'elemental'
    # Undead family
    if any(x in name for x in ['zombie', 'skeleton', 'ghoul', 'ghost', 'wight', 'wraith', 'vampire', 'lich', 'mummy']):
        return 'undead'
    # Beast family
    if any(x in name for x in ['wolf', 'bear', 'lion', 'tiger', 'snake', 'spider', 'rat', 'bat', 'hawk', 'eagle', 'boar', 'horse']):
        return 'beast'
    # Humanoid family
    if any(x in name for x in ['orc', 'goblin', 'hobgoblin', 'bugbear', 'gnoll', 'kobold', 'lizardfolk']):
        return 'humanoid'
    # Demon/Devil family
    if any(x in name for x in ['demon', 'devil', 'fiend', 'balor', 'pit fiend', 'vrock', 'hezrou']):
        return 'fiend'
    # Aberration family
    if any(x in name for x in ['beholder', 'mind flayer', 'aboleth', 'gith']):
        return 'aberration'

    return name  # Use the name itself as the family


# =============================================================================
# SPELL PARSERS
# =============================================================================

# Creatures per square foot baseline (3 creatures in 500 sq ft = 0.006)
CREATURES_PER_SQ_FT = 3 / 500


def estimate_aoe_targets(aoe_type, size_ft, width_ft=5):
    """
    Estimate number of creatures affected by an AoE spell.

    Args:
        aoe_type: Type of AoE ('radius', 'cone', 'line', 'cube', 'sphere', etc.)
        size_ft: Primary dimension in feet
        width_ft: Width for line spells (default 5ft)

    Returns:
        float: Estimated number of targets
    """
    import math

    if aoe_type in ('radius', 'sphere'):
        # Circle area: π × r²
        area = math.pi * (size_ft ** 2)
    elif aoe_type == 'cone':
        # Cone approximated as triangle: 0.5 × length × width_at_end
        # In D&D, cone width at end equals length
        area = 0.5 * size_ft * size_ft
    elif aoe_type == 'line':
        # Rectangle: length × width
        area = size_ft * width_ft
    elif aoe_type in ('cube', 'square'):
        # Square: side²
        area = size_ft ** 2
    elif aoe_type == 'cylinder':
        # Circle area (top-down view): π × r²
        area = math.pi * (size_ft ** 2)
    else:
        # Unknown type, estimate conservatively
        area = size_ft * 10  # Assume 10ft width

    estimated = area * CREATURES_PER_SQ_FT
    # Round to 1 decimal, minimum 1 target for any AoE
    return max(1, round(estimated, 1))


def parse_spell_targets(description):
    """
    Parse spell description to extract target information.

    Returns:
        dict with keys:
            - target_count: int or None (None for AoE)
            - is_aoe: bool
            - aoe_type: str ('cone', 'line', 'radius', 'cube', 'sphere', '')
            - aoe_size: str (e.g., '20-foot', '60-foot')
            - estimated_targets: float (for AoE, based on area)
    """
    if pd.isna(description):
        return {
            'target_count': None,
            'is_aoe': False,
            'aoe_type': '',
            'aoe_size': '',
            'estimated_targets': None
        }

    desc = str(description).lower()

    result = {
        'target_count': None,
        'is_aoe': False,
        'aoe_type': '',
        'aoe_size': '',
        'estimated_targets': None
    }

    # Check for AoE patterns first
    # Pattern for line with explicit dimensions (e.g., "100 feet long and 5 feet wide")
    line_match = re.search(r'(\d+)[- ]feet? long.*?(\d+)[- ]feet? wide', desc)
    if line_match:
        length = int(line_match.group(1))
        width = int(line_match.group(2))
        result['is_aoe'] = True
        result['aoe_type'] = 'line'
        result['aoe_size'] = f"{length}-foot"
        result['estimated_targets'] = estimate_aoe_targets('line', length, width)
        return result

    aoe_patterns = [
        (r'(\d+)-foot[- ]radius', 'radius'),
        (r'(\d+)-foot[- ]cone', 'cone'),
        (r'line[- ]of[- ](\d+)[- ]feet', 'line'),
        (r'(\d+)-foot[- ]line', 'line'),
        (r'(\d+)-foot[- ]cube', 'cube'),
        (r'(\d+)-foot[- ]sphere', 'sphere'),
        (r'(\d+)-foot[- ]square', 'square'),
        (r'(\d+)-foot[- ]cylinder', 'cylinder'),
    ]

    for pattern, aoe_type in aoe_patterns:
        match = re.search(pattern, desc)
        if match:
            size = int(match.group(1))
            result['is_aoe'] = True
            result['aoe_type'] = aoe_type
            result['aoe_size'] = f"{size}-foot"
            result['estimated_targets'] = estimate_aoe_targets(aoe_type, size)
            return result

    # Check for "each creature" patterns (also indicates AoE without explicit shape)
    if re.search(r'each creature (?:within|in|of your choice within)', desc):
        result['is_aoe'] = True
        result['aoe_type'] = 'area'
        result['estimated_targets'] = 3  # Default estimate for undefined AoE
        return result

    # Check for specific target counts
    # Patterns like "three darts", "three rays", "three bolts"
    number_words = {
        'one': 1, 'a ': 1, 'an ': 1,
        'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }

    # Look for "X darts/rays/bolts/beams/missiles" (allowing adjectives between)
    projectile_pattern = r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:\w+\s+)?(darts?|rays?|bolts?|beams?|missiles?|streaks?|projectiles?|arrows?)'
    match = re.search(projectile_pattern, desc)
    if match:
        count_str = match.group(1)
        if count_str in number_words:
            result['target_count'] = number_words[count_str]
        else:
            try:
                result['target_count'] = int(count_str)
            except ValueError:
                pass
        return result

    # Look for "up to X creatures/targets"
    up_to_pattern = r'up to (one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:creature|target|humanoid|willing creature)'
    match = re.search(up_to_pattern, desc)
    if match:
        count_str = match.group(1)
        if count_str in number_words:
            result['target_count'] = number_words[count_str]
        else:
            try:
                result['target_count'] = int(count_str)
            except ValueError:
                pass
        return result

    # Look for "X creatures/targets"
    creatures_pattern = r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:creature|target|humanoid|willing creature)s?(?:\s+(?:of your choice|you can see|within range))?'
    match = re.search(creatures_pattern, desc)
    if match:
        count_str = match.group(1)
        if count_str in number_words:
            result['target_count'] = number_words[count_str]
        else:
            try:
                result['target_count'] = int(count_str)
            except ValueError:
                pass
        return result

    # Single target patterns
    single_target_patterns = [
        r'a creature (?:you touch|within range|of your choice|you can see)',
        r'one creature',
        r'the target',
        r'choose a (?:creature|humanoid|target)',
        r'target a creature',
        r'creature you touch',
    ]

    for pattern in single_target_patterns:
        if re.search(pattern, desc):
            result['target_count'] = 1
            return result

    # Self-targeting spells
    if re.search(r'^(?:you |your )', desc) or 'range: self' in desc:
        result['target_count'] = 1
        return result

    return result
