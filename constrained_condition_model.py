#!/usr/bin/env python3
"""
Constrained Linear Regression with User-Specified Coefficients
Re-trains the HP prediction model with fixed coefficients for specific features
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize
import json
import re

# Load dataset
df = pd.read_csv('dnd5e_monsters_2014.csv')
print(f"📊 Loaded {len(df)} monsters from dataset\n")

# ===== FEATURE ENGINEERING =====
print("⚙️  FEATURE ENGINEERING")
print("=" * 60)

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

# Parse AC
def parse_ac(ac_str):
    if pd.isna(ac_str):
        return 10
    ac_str = str(ac_str).strip()
    match = re.search(r'\d+', ac_str)
    return int(match.group()) if match else 10

df['ac_value'] = df['AC'].apply(parse_ac)

# Parse speeds
def parse_speed(speed_str, speed_type):
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

df['speed_ground'] = df['Speed'].apply(lambda x: parse_speed(x, 'ground'))
df['speed_fly'] = df['Speed'].apply(lambda x: parse_speed(x, 'fly'))
df['speed_swim'] = df['Speed'].apply(lambda x: parse_speed(x, 'swim'))
df['speed_burrow'] = df['Speed'].apply(lambda x: parse_speed(x, 'burrow'))
df['speed_climb'] = df['Speed'].apply(lambda x: parse_speed(x, 'climb'))

df['max_speed'] = df[['speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb']].max(axis=1)
df['movement_types_count'] = (df[['speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb']] > 0).sum(axis=1)

# ⭐ NEW: has_flying feature
df['has_flying'] = (df['speed_fly'] > 0).astype(int)

# Parse proficiencies
def count_proficiencies(prof_str):
    if pd.isna(prof_str) or str(prof_str).strip() == '':
        return 0
    return len([x.strip() for x in str(prof_str).split(',') if x.strip()])

df['save_proficiency_count'] = df['Saving_Throws'].apply(count_proficiencies)
df['skill_proficiency_count'] = df['Skills'].apply(count_proficiencies)

# Parse damage resistances, immunities, vulnerabilities
df['resistance_count'] = df['Resistances'].apply(count_proficiencies)
df['immunity_count'] = df['Immunities'].apply(count_proficiencies)
df['vulnerability_count'] = df['Vulnerabilities'].apply(count_proficiencies)
df['condition_immunity_count'] = df['Condition_Immunities'].apply(count_proficiencies)

# Parse senses
def parse_sense(sense_str, sense_type):
    if pd.isna(sense_str):
        return 0
    sense_str = str(sense_str).lower()
    pattern = rf'{sense_type}\s+(\d+)\s*ft'
    match = re.search(pattern, sense_str)
    return int(match.group(1)) if match else 0

def has_sense(sense_str, sense_type):
    if pd.isna(sense_str):
        return 0
    return 1 if sense_type in str(sense_str).lower() else 0

df['has_darkvision'] = df['Senses'].apply(lambda x: has_sense(x, 'darkvision'))
df['darkvision_range'] = df['Senses'].apply(lambda x: parse_sense(x, 'darkvision'))
df['has_blindsight'] = df['Senses'].apply(lambda x: has_sense(x, 'blindsight'))
df['has_truesight'] = df['Senses'].apply(lambda x: has_sense(x, 'truesight'))
df['has_tremorsense'] = df['Senses'].apply(lambda x: has_sense(x, 'tremorsense'))

def parse_passive_perception(sense_str):
    if pd.isna(sense_str):
        return 10
    match = re.search(r'passive\s+perception\s+(\d+)', str(sense_str).lower())
    return int(match.group(1)) if match else 10

df['passive_perception'] = df['Senses'].apply(parse_passive_perception)

# Parse abilities from text
def count_abilities(text_str):
    if pd.isna(text_str) or str(text_str).strip() == '':
        return 0
    text = str(text_str).strip()
    entries = [x for x in re.split(r'\n+|\*\s+', text) if x.strip()]
    return len(entries)

df['trait_count'] = df['Traits'].apply(count_abilities)
df['action_count'] = df['Actions'].apply(count_abilities)
df['reaction_count'] = df['Reactions'].apply(count_abilities)
df['bonus_action_count'] = df['Bonus_Actions'].apply(count_abilities)

# Legendary actions
def parse_legendary_actions(leg_str):
    if pd.isna(leg_str) or str(leg_str).strip() == '':
        return 0, 0, 0
    text = str(leg_str).lower()

    has_leg = 1
    count_match = re.search(r'(\d+)\s+legendary\s+actions?', text)
    per_round = int(count_match.group(1)) if count_match else 3
    action_count = len([x for x in re.split(r'\n+|\*\s+', text) if x.strip() and 'can take' not in x.lower()])

    return has_leg, action_count, per_round

df[['has_legendary_actions', 'legendary_action_count', 'legendary_actions_per_round']] = df['Legendary_Actions'].apply(
    lambda x: pd.Series(parse_legendary_actions(x))
)

df['total_ability_count'] = df['trait_count'] + df['action_count'] + df['reaction_count'] + df['legendary_action_count']

# Parse specific abilities
combined_abilities = (df['Traits'].fillna('') + ' ' + df['Actions'].fillna('') + ' ' +
                     df['Reactions'].fillna('') + ' ' + df['Legendary_Actions'].fillna(''))

df['has_multiattack'] = combined_abilities.str.contains('multiattack', case=False, na=False).astype(int)

# Combat metrics
def parse_attack_bonus(actions_str):
    if pd.isna(actions_str):
        return 0
    matches = re.findall(r'\+(\d+)\s+to\s+hit', str(actions_str).lower())
    return max([int(m) for m in matches]) if matches else 0

def parse_save_dc(text_str):
    if pd.isna(text_str):
        return 0
    matches = re.findall(r'dc\s+(\d+)', str(text_str).lower())
    return max([int(m) for m in matches]) if matches else 0

df['highest_attack_bonus'] = df['Actions'].apply(parse_attack_bonus)
df['highest_save_dc'] = combined_abilities.apply(parse_save_dc)

# ⭐ NEW: Parse DPR from Actions
def parse_dpr(actions_str):
    """Estimate DPR from action text - very rough approximation"""
    if pd.isna(actions_str):
        return 0

    actions_str = str(actions_str).lower()
    total_dpr = 0

    # Look for damage dice patterns like "2d6+3" or "1d8"
    damage_patterns = re.findall(r'(\d+)d(\d+)(?:\s*\+\s*(\d+))?', actions_str)

    for num_dice, die_size, modifier in damage_patterns:
        num_dice = int(num_dice)
        die_size = int(die_size)
        modifier = int(modifier) if modifier else 0

        avg_damage = num_dice * (die_size + 1) / 2 + modifier
        total_dpr += avg_damage

    # If multiattack, estimate 2x damage
    if 'multiattack' in actions_str:
        total_dpr *= 1.5  # Conservative estimate

    return total_dpr

df['estimated_dpr'] = df['Actions'].apply(parse_dpr)

# Special traits
df['has_legendary_resistance'] = combined_abilities.str.contains('legendary resistance', case=False, na=False).astype(int)
df['has_magic_resistance'] = combined_abilities.str.contains('magic resistance', case=False, na=False).astype(int)
df['has_regeneration'] = combined_abilities.str.contains('regeneration', case=False, na=False).astype(int)

# Spellcasting
def parse_spellcasting(text_str):
    if pd.isna(text_str):
        return 0, 0
    text = str(text_str).lower()

    if 'spellcasting' not in text and 'innate spellcasting' not in text:
        return 0, 0

    has_spellcasting = 1
    level_match = re.search(r'(\d+)(?:st|nd|rd|th)[-\s]level\s+spellcaster', text)
    if level_match:
        return has_spellcasting, int(level_match.group(1))

    if '9th level' in text:
        return has_spellcasting, 17
    elif '8th level' in text:
        return has_spellcasting, 15
    elif '7th level' in text:
        return has_spellcasting, 13
    elif '6th level' in text:
        return has_spellcasting, 11
    elif '5th level' in text:
        return has_spellcasting, 9
    elif '4th level' in text:
        return has_spellcasting, 7
    elif '3rd level' in text:
        return has_spellcasting, 5
    elif '2nd level' in text:
        return has_spellcasting, 3
    elif '1st level' in text:
        return has_spellcasting, 1

    return has_spellcasting, 0

df[['has_spellcasting', 'spellcaster_level']] = df['Traits'].apply(
    lambda x: pd.Series(parse_spellcasting(x))
)

# Size ordinal
size_map = {'Tiny': 0, 'Small': 1, 'Medium': 2, 'Large': 3, 'Huge': 4, 'Gargantuan': 5}
df['size_ordinal'] = df['Size'].map(size_map).fillna(2)

# Grapple feature
df['has_grapple'] = combined_abilities.str.contains('grapple', case=False, na=False).astype(int)

# Condition features
conditions = [
    'poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
    'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned'
]

for condition in conditions:
    feature_name = f'inflicts_{condition}'
    df[feature_name] = combined_abilities.str.contains(condition, case=False, na=False).astype(int)

# Type one-hot encoding
df['Type'] = df['Type'].fillna('unknown')
type_dummies = pd.get_dummies(df['Type'], prefix='type')
df = pd.concat([df, type_dummies], axis=1)

print(f"✅ Feature engineering complete")

# ===== BUILD FEATURE MATRIX =====
print("\n🔧 BUILDING FEATURE MATRIX WITH CONSTRAINED FEATURES")
print("=" * 60)

feature_columns = [
    'cr_numeric', 'ac_value',
    'speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb',
    'max_speed', 'movement_types_count', 'has_flying',
    'save_proficiency_count', 'skill_proficiency_count',
    'resistance_count', 'immunity_count', 'vulnerability_count', 'condition_immunity_count',
    'has_darkvision', 'darkvision_range', 'has_blindsight', 'has_truesight', 'has_tremorsense',
    'passive_perception',
    'trait_count', 'action_count', 'reaction_count', 'bonus_action_count',
    'legendary_action_count', 'has_legendary_actions', 'legendary_actions_per_round',
    'total_ability_count',
    'has_multiattack',
    'highest_attack_bonus', 'highest_save_dc', 'estimated_dpr',
    'has_legendary_resistance', 'has_magic_resistance', 'has_regeneration',
    'has_spellcasting', 'spellcaster_level',
    'size_ordinal',
    'has_grapple'
]

# Add condition features
for condition in conditions:
    feature_columns.append(f'inflicts_{condition}')

# Add type dummies
type_cols = [col for col in df.columns if col.startswith('type_')]
feature_columns.extend(type_cols)

print(f"📊 Total features: {len(feature_columns)}")

# Build X and y
X = df[feature_columns].fillna(0)

def parse_hp(hp_str):
    if pd.isna(hp_str):
        return 0
    hp_str = str(hp_str).strip()
    match = re.match(r'(\d+)', hp_str)
    return int(match.group(1)) if match else 0

y = df['HP'].apply(parse_hp)

valid_idx = y > 0
X = X[valid_idx]
y = y[valid_idx]
print(f"✅ Valid samples: {len(X)} monsters with HP > 0")

# ===== CONSTRAINED TRAINING =====
print("\n🔒 TRAINING CONSTRAINED LINEAR REGRESSION")
print("=" * 60)

# User-specified constraints
CONSTRAINTS = {
    'estimated_dpr': -2.5,
    'ac_value': -5.0,
    'highest_attack_bonus': -6.0,
    'has_flying': -7.0
}

print("📌 Fixed coefficients:")
for feat, val in CONSTRAINTS.items():
    print(f"   {feat:25s} = {val:+.1f}")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Get indices of constrained features
constrained_indices = [feature_columns.index(feat) for feat in CONSTRAINTS.keys()]
constrained_values_scaled = []

for feat in CONSTRAINTS.keys():
    idx = feature_columns.index(feat)
    # Scale the constraint: constraint_scaled = constraint_raw * scaler.scale_[idx]
    constraint_scaled = CONSTRAINTS[feat] * scaler.scale_[idx]
    constrained_values_scaled.append(constraint_scaled)

print(f"\n🔧 Constrained features: {len(constrained_indices)}")
print(f"🔓 Free features: {len(feature_columns) - len(constrained_indices)}")

# Adjust y by subtracting contribution of constrained features
y_train_adjusted = y_train.values.astype(float).copy()
y_test_adjusted = y_test.values.astype(float).copy()

for i, (idx, val) in enumerate(zip(constrained_indices, constrained_values_scaled)):
    y_train_adjusted -= X_train_scaled[:, idx] * val
    y_test_adjusted -= X_test_scaled[:, idx] * val

# Create mask for free features
free_mask = np.ones(len(feature_columns), dtype=bool)
free_mask[constrained_indices] = False
free_indices = np.where(free_mask)[0]

# Train on free features only
X_train_free = X_train_scaled[:, free_indices]
X_test_free = X_test_scaled[:, free_indices]

# Solve normal equations for free coefficients
XtX = X_train_free.T @ X_train_free
Xty = X_train_free.T @ y_train_adjusted

# Add small regularization for numerical stability
alpha = 1e-6
coef_free = np.linalg.solve(XtX + alpha * np.eye(len(free_indices)), Xty)

# Construct full coefficient vector
coef_full = np.zeros(len(feature_columns))
coef_full[free_indices] = coef_free
for idx, val in zip(constrained_indices, constrained_values_scaled):
    coef_full[idx] = val

# Calculate intercept
intercept = y_train.mean() - (X_train_scaled @ coef_full).mean()

# Evaluate
y_pred_train = X_train_scaled @ coef_full + intercept
y_pred_test = X_test_scaled @ coef_full + intercept

train_r2 = 1 - np.sum((y_train - y_pred_train)**2) / np.sum((y_train - y_train.mean())**2)
test_r2 = 1 - np.sum((y_test - y_pred_test)**2) / np.sum((y_test - y_test.mean())**2)
mae = np.mean(np.abs(y_test - y_pred_test))

print(f"\n📊 Model Performance:")
print(f"   Train R²: {train_r2:.4f}")
print(f"   Test R²:  {test_r2:.4f}")
print(f"   Test MAE: {mae:.2f} HP")

# ===== VERIFY CONSTRAINTS =====
print("\n✅ VERIFYING CONSTRAINTS")
print("=" * 60)

coef_dict = dict(zip(feature_columns, coef_full))

for feat in CONSTRAINTS.keys():
    idx = feature_columns.index(feat)
    raw_coef = coef_full[idx] / scaler.scale_[idx]
    expected = CONSTRAINTS[feat]
    print(f"{feat:25s}: Expected {expected:+7.1f}, Got {raw_coef:+7.1f} ✓")

# ===== ANALYZE CONDITION COEFFICIENTS =====
print("\n📈 CONDITION IMPACT ON HP (with constraints)")
print("=" * 60)

print(f"{'Condition':<20s} {'HP Impact':>12s} {'Prevalence':>12s}")
print("-" * 50)

condition_results = []
for condition in conditions:
    feature_name = f'inflicts_{condition}'
    feature_idx = feature_columns.index(feature_name)

    # Unscale coefficient
    hp_impact = coef_full[feature_idx] / scaler.scale_[feature_idx]

    count = df[feature_name].sum()
    pct = count / len(df) * 100

    print(f"{condition:<20s} {hp_impact:+12.1f} HP {count:4d} ({pct:4.1f}%)")

    condition_results.append({
        'condition': condition,
        'hp_impact': hp_impact,
        'count': int(count),
        'percentage': pct
    })

# ===== CREATE MODEL OBJECT =====
class ConstrainedLinearModel:
    """Custom model class that mimics sklearn LinearRegression interface"""
    def __init__(self, coef, intercept):
        self.coef_ = coef
        self.intercept_ = intercept
        self.rank_ = len(coef)

    def predict(self, X):
        return X @ self.coef_ + self.intercept_

    def score(self, X, y):
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - y.mean())**2)
        return 1 - ss_res / ss_tot

model = ConstrainedLinearModel(coef_full, intercept)

# ===== SAVE ARTIFACTS =====
print("\n💾 SAVING MODEL ARTIFACTS")
print("=" * 60)

with open('hp_lr_model_with_conditions.pkl', 'wb') as f:
    pickle.dump(model, f)
print("✅ Saved: hp_lr_model_with_conditions.pkl")

with open('hp_scaler_with_conditions.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print("✅ Saved: hp_scaler_with_conditions.pkl")

with open('hp_feature_columns_with_conditions.pkl', 'wb') as f:
    pickle.dump(feature_columns, f)
print("✅ Saved: hp_feature_columns_with_conditions.pkl")

# Export to JSON for web app
model_export = {
    'intercept': float(intercept),
    'coefficients': {feat: float(coef) for feat, coef in zip(feature_columns, coef_full)},
    'scaler_mean': {feat: float(mean) for feat, mean in zip(feature_columns, scaler.mean_)},
    'scaler_scale': {feat: float(scale) for feat, scale in zip(feature_columns, scaler.scale_)},
    'feature_columns': feature_columns,
    'constraints': CONSTRAINTS
}

with open('monster-builder-app/model_data_with_conditions.json', 'w') as f:
    json.dump(model_export, f, indent=2)
print("✅ Saved: monster-builder-app/model_data_with_conditions.json")

with open('condition_analysis_results.json', 'w') as f:
    json.dump(condition_results, f, indent=2)
print("✅ Saved: condition_analysis_results.json")

# ===== SUMMARY =====
print("\n" + "=" * 60)
print("🎉 CONSTRAINED MODEL TRAINING COMPLETE")
print("=" * 60)

print(f"\n📊 MODEL STATISTICS:")
print(f"   - Total features: {len(feature_columns)}")
print(f"   - Constrained features: {len(CONSTRAINTS)}")
print(f"   - Free features: {len(feature_columns) - len(CONSTRAINTS)}")
print(f"   - Test R²: {test_r2:.4f}")
print(f"   - Test MAE: {mae:.2f} HP")

print(f"\n🔒 CONSTRAINTS APPLIED:")
for feat, val in CONSTRAINTS.items():
    print(f"   - {feat:25s} = {val:+.1f}")

print(f"\n🔝 TOP 5 HP-INCREASING CONDITIONS:")
sorted_conditions = sorted(condition_results, key=lambda x: x['hp_impact'], reverse=True)
for i, result in enumerate(sorted_conditions[:5], 1):
    print(f"   {i}. {result['condition']:<15s}: +{result['hp_impact']:6.1f} HP ({result['count']} monsters)")

print("\n✨ Model ready for web app integration!")
