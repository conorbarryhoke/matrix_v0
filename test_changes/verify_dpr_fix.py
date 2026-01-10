"""
Verify DPR fix by comparing old vs new DPR values for problematic creatures.
Run this before executing the full notebook.
"""
import pandas as pd
import json
import re

def calculate_average_damage(damage_str):
    """Calculate average damage from dice notation like '2d8 + 5'"""
    if not damage_str:
        return 0
    
    total = 0
    patterns = re.findall(r'(\d+)d(\d+)(?:\s*[+\-]\s*(\d+))?', str(damage_str))
    
    for match in patterns:
        num_dice = int(match[0])
        die_size = int(match[1])
        modifier = int(match[2]) if match[2] else 0
        avg = num_dice * (die_size + 1) / 2 + modifier
        total += avg
    
    return total

def parse_dpr_OLD(actions_str):
    """Old buggy version"""
    if pd.isna(actions_str):
        return 0
    
    try:
        actions = json.loads(actions_str)
    except:
        return 0
    
    attack_damages = {}
    multiattack_desc = None
    
    for action in actions:
        if not isinstance(action, dict):
            continue
        
        name = action.get('Name', '').lower()
        
        if name == 'multiattack':
            multiattack_desc = action.get('Desc', '').lower()
        elif 'Damage' in action:
            damage = calculate_average_damage(action.get('Damage', ''))
            if 'Damage 2' in action:
                damage += calculate_average_damage(action.get('Damage 2', ''))
            attack_damages[name] = damage
    
    if not attack_damages:
        return 0
    
    if not multiattack_desc:
        return max(attack_damages.values())
    
    total_dpr = 0
    
    # Old buggy logic - fallback triggers too early
    match = re.search(r'makes?\s+(\w+)\s+attacks?', multiattack_desc)
    if match:
        count_word = match.group(1).lower()
        number_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
        count = number_map.get(count_word, 2)
        total_dpr = count * max(attack_damages.values())
    else:
        total_dpr = 2 * max(attack_damages.values())
    
    return total_dpr

def parse_dpr_NEW(actions_str):
    """New fixed version"""
    if pd.isna(actions_str):
        return 0
    
    try:
        actions = json.loads(actions_str)
    except:
        return 0
    
    attack_damages = {}
    multiattack_desc = None
    
    for action in actions:
        if not isinstance(action, dict):
            continue
        
        name = action.get('Name', '').lower()
        
        if name == 'multiattack':
            multiattack_desc = action.get('Desc', '').lower()
        elif 'Damage' in action:
            damage = calculate_average_damage(action.get('Damage', ''))
            if 'Damage 2' in action:
                damage += calculate_average_damage(action.get('Damage 2', ''))
            attack_damages[name] = damage
    
    if not attack_damages:
        return 0
    
    if not multiattack_desc:
        return max(attack_damages.values())
    
    total_dpr = 0
    attacks_counted = set()
    
    # Try specific attack matching first
    for attack_name, damage in attack_damages.items():
        patterns = [
            rf'(\w+)\s+{re.escape(attack_name)}\s+attacks?',
            rf'(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}',
            rf'makes?\s+(\w+)\s+{re.escape(attack_name)}\s+attacks?',
            rf'makes?\s+(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, multiattack_desc)
            if match:
                count_word = match.group(1).lower()
                number_map = {'one': 1, 'a': 1, 'an': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
                count = number_map.get(count_word, 0)
                if count == 0:
                    try:
                        count = int(count_word)
                    except ValueError:
                        count = 0
                
                if count > 0:
                    total_dpr += count * damage
                    attacks_counted.add(attack_name)
                    break
    
    if total_dpr > 0:
        return total_dpr
    
    # Improved fallback
    if len(attack_damages) == 1:
        match = re.search(r'makes?\s+(\w+)\s+attacks?', multiattack_desc)
        if match:
            count_word = match.group(1).lower()
            number_map = {'one': 1, 'a': 1, 'an': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
            count = number_map.get(count_word, 2)
            
            for attack_name in attack_damages.keys():
                if f'with its {attack_name}' not in multiattack_desc and f'{attack_name} attacks' not in multiattack_desc:
                    if re.search(rf'(one|a|an|two|three)\s+(?:attack\s+with\s+(?:its\s+)?)?{re.escape(attack_name)}', multiattack_desc):
                        return max(attack_damages.values())
            
            total_dpr = count * max(attack_damages.values())
    else:
        total_dpr = 2 * max(attack_damages.values())
    
    return total_dpr

# Load creatures
df = pd.read_csv('../data/dnd5e_monsters_from_json.csv')

# Test problematic creatures
test_creatures = ['Roper', 'Gibbering Mouther', 'Shield Guardian']

print("=" * 80)
print("DPR PARSING COMPARISON: OLD vs NEW")
print("=" * 80)
print()

changes = []
for creature_name in test_creatures:
    creature = df[df['Name'] == creature_name]
    if creature.empty:
        print(f"❌ {creature_name} not found")
        continue
    
    creature = creature.iloc[0]
    actions = creature['Actions']
    
    old_dpr = parse_dpr_OLD(actions)
    new_dpr = parse_dpr_NEW(actions)
    
    changed = old_dpr != new_dpr
    status = "🔧 CHANGED" if changed else "✓ Same"
    
    print(f"{status} - {creature_name}")
    print(f"  Old DPR: {old_dpr}")
    print(f"  New DPR: {new_dpr}")
    if changed:
        print(f"  Diff: {new_dpr - old_dpr:+.1f}")
        changes.append((creature_name, old_dpr, new_dpr))
    print()

print("=" * 80)
print(f"Summary: {len(changes)} creatures will have DPR changes")
print("=" * 80)

if changes:
    print("\nCreatures with DPR changes:")
    for name, old, new in changes:
        print(f"  - {name}: {old} → {new} ({new - old:+.1f})")

