#!/usr/bin/env python3
"""
Feature Engineering: Condition-Inflicting Abilities
Analyzes HP impact of creatures that can inflict various conditions
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import json
import re

# Load dataset
df = pd.read_csv('data/dnd5e_monsters_2014.csv')
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
    # Count entries separated by line breaks or bullet points
    text = str(text_str).strip()
    entries = [x for x in re.split(r'\n+|\*\s+', text) if x.strip()]
    return len(entries)

df['action_count'] = df['Actions'].apply(count_abilities)
df['reaction_count'] = df['Reactions'].apply(count_abilities)
df['bonus_action_count'] = df['Bonus_Actions'].apply(count_abilities)

# Legendary actions
def parse_legendary_actions(leg_str):
    if pd.isna(leg_str) or str(leg_str).strip() == '':
        return 0, 0, 0
    text = str(leg_str).lower()

    # Has legendary actions
    has_leg = 1

    # Count number of legendary actions
    count_match = re.search(r'(\d+)\s+legendary\s+actions?', text)
    per_round = int(count_match.group(1)) if count_match else 3

    # Count distinct legendary action options
    action_count = len([x for x in re.split(r'\n+|\*\s+', text) if x.strip() and 'can take' not in x.lower()])

    return has_leg, action_count, per_round

df[['has_legendary_actions', 'legendary_action_count', 'legendary_actions_per_round']] = df['Legendary_Actions'].apply(
    lambda x: pd.Series(parse_legendary_actions(x))
)


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

    # Try to extract spellcaster level
    level_match = re.search(r'(\d+)(?:st|nd|rd|th)[-\s]level\s+spellcaster', text)
    if level_match:
        return has_spellcasting, int(level_match.group(1))

    # Estimate from spell slots mentioned
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

# ⭐ NEW FEATURE: has_grapple (from previous work)
df['has_grapple'] = combined_abilities.str.contains('grapple', case=False, na=False).astype(int)

# ⭐⭐ NEW FEATURES: Condition-inflicting abilities
print("\n🎯 ANALYZING CONDITION-INFLICTING ABILITIES")
print("=" * 60)

conditions = [
    'poisoned',
    'blinded',
    'charmed',
    'deafened',
    'frightened',
    'incapacitated',
    'paralyzed',
    'petrified',
    'prone',
    'restrained',
    'stunned'
]

for condition in conditions:
    feature_name = f'inflicts_{condition}'
    df[feature_name] = combined_abilities.str.contains(condition, case=False, na=False).astype(int)
    count = df[feature_name].sum()
    pct = count / len(df) * 100
    print(f"✨ {feature_name:25s}: {count:3d} / {len(df)} ({pct:5.1f}%)")

# Type one-hot encoding
df['Type'] = df['Type'].fillna('unknown')
type_dummies = pd.get_dummies(df['Type'], prefix='type')
df = pd.concat([df, type_dummies], axis=1)

print(f"\n✅ Feature engineering complete: {len(df.columns)} total columns")

# ===== BUILD FEATURE MATRIX =====
print("\n🔧 BUILDING FEATURE MATRIX")
print("=" * 60)

# Define feature columns
feature_columns = [
    'cr_numeric', 'ac_value',
    'speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb',
    'max_speed', 'movement_types_count',
    'save_proficiency_count', 'skill_proficiency_count',
    'resistance_count', 'immunity_count', 'vulnerability_count', 'condition_immunity_count',
    'has_darkvision', 'darkvision_range', 'has_blindsight', 'has_truesight', 'has_tremorsense',
    'passive_perception',
    'action_count', 'reaction_count', 'bonus_action_count',
    'legendary_action_count', 'has_legendary_actions', 'legendary_actions_per_round',
    'has_multiattack',
    'highest_attack_bonus', 'highest_save_dc',
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
print(f"   - Base features: {len(feature_columns) - len(type_cols) - len(conditions)}")
print(f"   - Condition features: {len(conditions)}")
print(f"   - Type features: {len(type_cols)}")

# Build X and y
X = df[feature_columns].fillna(0)

# Parse HP (may contain dice notation like "45 (6d10+12)")
def parse_hp(hp_str):
    if pd.isna(hp_str):
        return 0
    hp_str = str(hp_str).strip()
    match = re.match(r'(\d+)', hp_str)
    return int(match.group(1)) if match else 0

y = df['HP'].apply(parse_hp)

# Remove rows with HP = 0
valid_idx = y > 0
X = X[valid_idx]
y = y[valid_idx]
print(f"\n✅ Valid samples: {len(X)} monsters with HP > 0")

# ===== TRAIN MODEL =====
print("\n🤖 TRAINING LINEAR REGRESSION MODEL")
print("=" * 60)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_scaled, y_train)

# Evaluate
train_score = model.score(X_train_scaled, y_train)
test_score = model.score(X_test_scaled, y_test)
y_pred = model.predict(X_test_scaled)
mae = np.mean(np.abs(y_test - y_pred))

print(f"Train R²: {train_score:.4f}")
print(f"Test R²:  {test_score:.4f}")
print(f"Test MAE: {mae:.2f} HP")

# ===== ANALYZE CONDITION COEFFICIENTS =====
print("\n📈 CONDITION IMPACT ON HP")
print("=" * 60)

coef_dict = dict(zip(feature_columns, model.coef_))

print(f"{'Condition':<20s} {'Coefficient':>12s} {'HP Impact':>12s} {'Prevalence':>12s}")
print("-" * 60)

condition_results = []
for condition in conditions:
    feature_name = f'inflicts_{condition}'
    coef = coef_dict.get(feature_name, 0)

    # HP impact (scaled coefficient)
    # Scale back: multiply by scaler.scale_[feature_idx]
    feature_idx = feature_columns.index(feature_name)
    scale = scaler.scale_[feature_idx]
    hp_impact = coef / scale if scale > 0 else 0

    count = df[feature_name].sum()
    pct = count / len(df) * 100

    print(f"{condition:<20s} {coef:+12.4f} {hp_impact:+12.1f} HP {count:4d} ({pct:4.1f}%)")

    condition_results.append({
        'condition': condition,
        'coefficient': coef,
        'hp_impact': hp_impact,
        'count': int(count),
        'percentage': pct
    })

# ===== SAVE ARTIFACTS =====
print("\n💾 SAVING MODEL ARTIFACTS")
print("=" * 60)

# Save model
with open('pickled_models/hp_lr_model_with_conditions.pkl', 'wb') as f:
    pickle.dump(model, f)
print("✅ Saved: pickled_models/hp_lr_model_with_conditions.pkl")

# Save scaler
with open('pickled_models/hp_scaler_with_conditions.pkl', 'wb') as f:
    pickle.dump(scaler, f)
print("✅ Saved: pickled_models/hp_scaler_with_conditions.pkl")

# Save feature columns
with open('pickled_models/hp_feature_columns_with_conditions.pkl', 'wb') as f:
    pickle.dump(feature_columns, f)
print("✅ Saved: pickled_models/hp_feature_columns_with_conditions.pkl")

# Export to JSON for web app
model_export = {
    'intercept': float(model.intercept_),
    'coefficients': {feat: float(coef) for feat, coef in zip(feature_columns, model.coef_)},
    'scaler_mean': {feat: float(mean) for feat, mean in zip(feature_columns, scaler.mean_)},
    'scaler_scale': {feat: float(scale) for feat, scale in zip(feature_columns, scaler.scale_)},
    'feature_columns': feature_columns
}

with open('monster-builder-app/model_data_with_conditions.json', 'w') as f:
    json.dump(model_export, f, indent=2)
print("✅ Saved: monster-builder-app/model_data_with_conditions.json")

# Save condition analysis results
with open('data/condition_analysis_results.json', 'w') as f:
    json.dump(condition_results, f, indent=2)
print("✅ Saved: data/condition_analysis_results.json")

# ===== SUMMARY =====
print("\n" + "=" * 60)
print("🎉 CONDITION FEATURE ENGINEERING COMPLETE")
print("=" * 60)

print(f"\n📊 MODEL STATISTICS:")
print(f"   - Total features: {len(feature_columns)}")
print(f"   - Condition features added: {len(conditions)}")
print(f"   - Test R²: {test_score:.4f}")
print(f"   - Test MAE: {mae:.2f} HP")

print(f"\n🔝 TOP 5 HP-INCREASING CONDITIONS:")
sorted_conditions = sorted(condition_results, key=lambda x: x['hp_impact'], reverse=True)
for i, result in enumerate(sorted_conditions[:5], 1):
    print(f"   {i}. {result['condition']:<15s}: +{result['hp_impact']:6.1f} HP ({result['count']} monsters)")

print(f"\n🔻 TOP 5 HP-DECREASING CONDITIONS:")
for i, result in enumerate(sorted_conditions[-5:], 1):
    print(f"   {i}. {result['condition']:<15s}: {result['hp_impact']:+6.1f} HP ({result['count']} monsters)")

print("\n✨ Ready to integrate into web app!")
