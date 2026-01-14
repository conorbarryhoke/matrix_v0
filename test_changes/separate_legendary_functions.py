#!/usr/bin/env python3
"""
Separate parse_legendary_actions_dpr into two functions:
1. parse_legendary_actions_dpr - returns only max_damage
2. parse_legendary_conditions - returns list of conditions
"""

import json
import re

def separate_functions():
    # Load notebook
    with open('notebooks/three_tier_hp_model_v2.ipynb', 'r') as f:
        nb = json.load(f)

    # Find the cell with parse_legendary_actions_dpr definition
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])

            # Check if this is the parser function definition cell
            if 'def parse_legendary_actions_dpr(legendary_str):' in source:
                print(f"Found parser function in cell {i}")

                # Create the new separated functions
                new_source = """# Legendary Actions Parsers - separated for maintainability"""

def parse_legendary_conditions(legendary_str):
    """
    Parse legendary actions to extract conditions inflicted.
    Returns: list of condition strings
    """
    if pd.isna(legendary_str) or str(legendary_str).strip() == '':
        return []

    text = str(legendary_str)

    # Split into individual legendary actions
    action_blocks = re.split(r'\\n\\s*\\n|\\n\\*\\s*', text)

    conditions_found = []

    condition_keywords = [
        'poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
        'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned'
    ]

    for block in action_blocks:
        if not block.strip():
            continue

        # Skip the preamble text
        if 'can take' in block.lower() or 'only one legendary action' in block.lower():
            continue

        # Parse conditions inflicted
        for condition in condition_keywords:
            if condition in block.lower():
                conditions_found.append(condition)

    return list(set(conditions_found))


def parse_legendary_actions_dpr(legendary_str):
    """
    Parse legendary actions to calculate maximum DPR.
    Returns: float (max damage per round)

    Uses knapsack-style optimization to find damage-maximizing combination within action budget.
    """
    if pd.isna(legendary_str) or str(legendary_str).strip() == '':
        return 0

    text = str(legendary_str)

    # Determine action budget (default 3)
    budget_match = re.search(r'(\\d+)\\s+legendary\\s+actions?', text.lower())
    action_budget = int(budget_match.group(1)) if budget_match else 3

    # Split into individual legendary actions
    # Actions are typically separated by double newlines or asterisks
    action_blocks = re.split(r'\\n\\s*\\n|\\n\\*\\s*', text)

    legendary_actions = []

    for block in action_blocks:
        if not block.strip():
            continue

        # Skip the preamble text
        if 'can take' in block.lower() or 'only one legendary action' in block.lower():
            continue

        # Parse action cost (default 1)
        cost_match = re.search(r'\\(costs?\\s+(\\d+)\\s+actions?\\)', block, re.IGNORECASE)
        cost = int(cost_match.group(1)) if cost_match else 1

        # Parse damage from dice notation
        damage = 0
        # Find all damage dice patterns (e.g., "17 (2d6 + 10)" or "2d8+5")
        damage_matches = re.findall(r'(\\d+)\\s*\\((\\d+d\\d+(?:\\s*[+\\-]\\s*\\d+)?)\\)', block)
        if damage_matches:
            # Use the average from the first match (number before parentheses)
            damage = int(damage_matches[0][0])
        else:
            # Try to find bare dice notation
            dice_matches = re.findall(r'(\\d+)d(\\d+)(?:\\s*[+\\-]\\s*(\\d+))?', block)
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

    # Knapsack-style optimization: find damage-maximizing combination
    # dp[i] = (max_damage, actions_used)
    dp = {0: (0, [])}

    for action in legendary_actions:
        cost = action['cost']
        damage = action['damage']

        # Update dp table
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
"""

                # Update the cell source
                cell['source'] = new_source.split('\n')
                # Add newline to each line except the last
                cell['source'] = [line + '\n' for line in cell['source'][:-1]] + [cell['source'][-1]]

                print("✅ Updated parser function cell")

            # Check if this is the usage cell
            if "legendary_results = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)" in source:
                print(f"Found usage cell {i}")

                # Update the usage
                new_usage = """

# Parse legendary actions for DPR and conditions
df['legendary_dpr'] = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)
df['legendary_conditions'] = df['Legendary_Actions'].apply(parse_legendary_conditions)

# Calculate total DPR (regular actions + legendary actions)
df['total_dpr'] = df['estimated_dpr'] + df['legendary_dpr']

# Special traits
df['has_legendary_resistance'] = combined_abilities.str.contains('legendary resistance', case=False, na=False).astype(int)
df['has_magic_resistance'] = combined_abilities.str.contains('magic resistance', case=False, na=False).astype(int)
df['has_regeneration'] = combined_abilities.str.contains('regeneration', case=False, na=False).astype(int)

# Replace the relevant section
old_pattern = r"# Parse legendary actions for DPR and conditions\nlegendary_results = df\['Legendary_Actions'\]\.apply\(parse_legendary_actions_dpr\)\ndf\['legendary_dpr'\] = legendary_results\.apply\(lambda x: x\[0\]\)\ndf\['legendary_conditions'\] = legendary_results\.apply\(lambda x: x\[1\]\)\n\n# Calculate total DPR.*?\n# Special traits\ndf\['has_legendary_resistance'\] = combined_abilities\.str\.contains\('legendary resistance', case=False, na=False\)\.astype\(int\)\ndf\['has_magic_resistance'\] = combined_abilities\.str\.contains\('magic resistance', case=False, na=False\)\.astype\(int\)\ndf\['has_regeneration'\] = combined_abilities\.str\.contains\('regeneration', case=False, na=False\)\.astype\(int\)"

# Simpler approach: reconstruct the section
if "legendary_results = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)" in source:
    lines = source.split('\n')
    new_lines = []
    skip_until = -1

    for idx, line in enumerate(lines):
        if idx < skip_until:
            continue

        if "legendary_results = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)" in line:
            # Replace the next 2 lines as well
            new_lines.append("# Parse legendary actions for DPR and conditions")
            new_lines.append("df['legendary_dpr'] = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)")
            new_lines.append("df['legendary_conditions'] = df['Legendary_Actions'].apply(parse_legendary_conditions)")
            skip_until = idx + 3  # Skip the next 2 lines (legendary_dpr and legendary_conditions assignments)
        else:
            new_lines.append(line)

    new_source = '\n'.join(new_lines)
    cell['source'] = new_source.split('\n')
    cell['source'] = [line + '\n' for line in cell['source'][:-1]] + [cell['source'][-1]]

    print("✅ Updated usage cell")

    # Save the modified notebook
    with open('notebooks/three_tier_hp_model_v2.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)

    print("\n✅ Successfully separated functions!")
    print("   - parse_legendary_actions_dpr() now returns only max_damage")
    print("   - parse_legendary_conditions() extracts conditions")
    print("   - Usage updated to call both functions separately")

if __name__ == '__main__':
    separate_functions()
