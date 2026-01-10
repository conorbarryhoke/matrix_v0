"""Test DPR parsing improvements"""
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

def parse_dpr_from_json_FIXED(actions_str):
    """
    FIXED VERSION: Parse DPR from JSON action structures.
    Handles multiattack and calculates total DPR.
    """
    if not actions_str or str(actions_str).strip() == '':
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
            
            # Add secondary damage if present
            if 'Damage 2' in action:
                damage += calculate_average_damage(action.get('Damage 2', ''))
            
            attack_damages[name] = damage
    
    # If no attacks found, return 0
    if not attack_damages:
        return 0
    
    # If no multiattack, return highest single attack damage
    if not multiattack_desc:
        return max(attack_damages.values())
    
    # Parse multiattack description to determine attack counts
    total_dpr = 0
    attacks_counted = set()
    
    # FIX: Try to match specific attacks mentioned in multiattack
    for attack_name, damage in attack_damages.items():
        # Look for patterns like "two beak attacks", "one with its bite", "makes one bite attack"
        patterns = [
            rf'(\w+)\s+{re.escape(attack_name)}\s+attacks?',  # "four bite attacks"
            rf'(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}',  # "four attacks with its bite"
            rf'makes?\s+(\w+)\s+{re.escape(attack_name)}\s+attacks?',  # "makes one bite attack"
            rf'makes?\s+(\w+)\s+attacks?\s+with\s+(?:its\s+)?{re.escape(attack_name)}',  # "makes one attack with its bite"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, multiattack_desc)
            if match:
                count_word = match.group(1).lower()
                # Convert word to number
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
                    attacks_counted.add(attack_name)
                    break
    
    # If we found specific attacks, return that total
    if total_dpr > 0:
        return total_dpr
    
    # FIX: If no specific attacks matched, check if generic "makes X attacks" refers to damaging attacks
    # Only use fallback if there's EXACTLY ONE damaging attack type
    if len(attack_damages) == 1:
        match = re.search(r'makes?\s+(\w+)\s+attacks?', multiattack_desc)
        if match:
            count_word = match.group(1).lower()
            number_map = {
                'one': 1, 'a': 1, 'an': 1, 'two': 2, 'three': 3,
                'four': 4, 'five': 5, 'six': 6
            }
            count = number_map.get(count_word, 2)  # Default to 2 if not found
            
            # Check that the generic count isn't referring to a different attack type
            # e.g., "makes four attacks with its tendrils" where tendrils don't do damage
            for attack_name in attack_damages.keys():
                # If the multiattack mentions a different attack type after "makes X attacks"
                # then the count doesn't apply to our damaging attack
                if f'with its {attack_name}' not in multiattack_desc and f'{attack_name} attacks' not in multiattack_desc:
                    # The generic count might be for a non-damaging attack
                    # Look for specific mention of our damaging attack
                    if re.search(rf'(one|a|an|two|three)\s+(?:attack\s+with\s+(?:its\s+)?)?{re.escape(attack_name)}', multiattack_desc):
                        # Found a specific count for our attack, don't use generic fallback
                        return max(attack_damages.values())  # Default to 1 attack
            
            total_dpr = count * max(attack_damages.values())
    else:
        # Multiple damaging attacks, can't use generic fallback safely
        # Default: assume 2 attacks with highest damage
        total_dpr = 2 * max(attack_damages.values())
    
    return total_dpr


# Test cases
test_cases = [
    {
        'name': 'Roper',
        'actions': '[{"Name":"Multiattack","Desc":"The roper makes four attacks with its tendrils, uses Reel, and makes one attack with its bite."},{"Name":"Bite","Type Attack":"Weapon Attack","Type":"Melee","Hit Bonus":"7","Reach":"5 ft.","Target":"one target","Damage":"4d8 + 4","Damage Type":"piercing"},{"Name":"Tendril","Type Attack":"Weapon Attack","Type":"Melee","Hit Bonus":"7","Reach":"50 ft.","Target":"one creature","Desc":"The target is grappled (escape dc 15) Until the grapple ends, the target is restrained and has disadvantage on Strength checks and Strength saving throws, and the roper can\'t use the same tendril on another target"},{"Name":"Reel","Desc":"The roper pulls each creature grappled by it up to 25 ft. straight toward it."}]',
        'expected': 22.0,
        'note': 'Four tendrils (no damage), one bite (22 damage)'
    },
    {
        'name': 'Simple multiattack',
        'actions': '[{"Name":"Multiattack","Desc":"The creature makes two attacks with its claws."},{"Name":"Claw","Damage":"2d6 + 3"}]',
        'expected': 20.0,
        'note': 'Two claw attacks at 10 damage each'
    },
    {
        'name': 'No multiattack',
        'actions': '[{"Name":"Bite","Damage":"2d8 + 4"}]',
        'expected': 13.0,
        'note': 'Single attack'
    }
]

print("=" * 80)
print("DPR PARSER FIX VERIFICATION")
print("=" * 80)
print()

all_passed = True
for test in test_cases:
    result = parse_dpr_from_json_FIXED(test['actions'])
    passed = result == test['expected']
    all_passed = all_passed and passed
    
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test['name']}")
    print(f"  Expected: {test['expected']}")
    print(f"  Got: {result}")
    print(f"  Note: {test['note']}")
    print()

print("=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 80)
