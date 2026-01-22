"""
Parsing functions for the HP prediction model.

This module contains all functions that parse raw creature data
(strings, JSON) into numeric features for the model.
"""

import re
import json
import pandas as pd


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
    Parse bonus action attacks from charge/pounce/rampage traits.
    Returns additional DPR from these conditional attacks.

    Handles:
    - Trampling Charge (Elephant, Mammoth, etc.) - ~50% chance
    - Pounce (Lion, Tiger, etc.) - ~50% chance
    - Rampage (Gnoll, Giant Hyena) - ~25% chance (requires reducing to 0 HP)
    """
    if pd.isna(traits_str) or pd.isna(actions_str):
        return 0

    try:
        traits = json.loads(traits_str)
        actions = json.loads(actions_str)
    except (json.JSONDecodeError, TypeError):
        return 0

    # Build attack damage map
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

        # Check for charge/pounce abilities
        if any(x in trait_name for x in ['charge', 'pounce']):
            match = re.search(r'can make (?:one|an?|another) (\w+) attack', trait_desc)
            if not match:
                match = re.search(r'can make (?:one|an?|another) attack with (?:its )?(\w+)', trait_desc)
            if match:
                attack_name = match.group(1).lower()
                for action_name, damage in attack_damages.items():
                    if attack_name in action_name:
                        # 50% chance for charge/pounce
                        bonus_dpr += damage * 0.5
                        break

        # Check for rampage ability
        elif 'rampage' in trait_name:
            match = re.search(r'make (?:a|an?) (\w+) attack', trait_desc)
            if match:
                attack_name = match.group(1).lower()
                for action_name, damage in attack_damages.items():
                    if attack_name in action_name:
                        # 25% chance for rampage
                        bonus_dpr += damage * 0.25
                        break

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
