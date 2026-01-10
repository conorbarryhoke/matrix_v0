#!/usr/bin/env python3
"""
Test script to verify the sequential three-phase HP model for an Owlbear.
Shows step-by-step breakdown of Phase 1, Phase 2, and Phase 3 predictions.
"""

import pandas as pd
import numpy as np
import pickle
import json
from scipy.interpolate import interp1d
import re

# Load the trained models
print("=" * 80)
print("LOADING MODELS")
print("=" * 80)

with open('pickled_models/hp_model_low_cr.pkl', 'rb') as f:
    model_low = pickle.load(f)
    print("✅ Loaded Low-CR model")

with open('pickled_models/hp_model_mid_cr.pkl', 'rb') as f:
    model_mid = pickle.load(f)
    print("✅ Loaded Mid-CR model")

with open('pickled_models/hp_model_high_cr.pkl', 'rb') as f:
    model_high = pickle.load(f)
    print("✅ Loaded High-CR model")

# Load baseline data
with open('data/baseline_lookup_three_tier.json', 'r') as f:
    baseline_data = json.load(f)
    print("✅ Loaded baseline data")

# Create interpolation functions
cr_values = np.array(baseline_data['cr_values'])
hp_baseline_interp = interp1d(cr_values, baseline_data['hp_baseline'],
                               kind='linear', bounds_error=False, fill_value='extrapolate')
ac_baseline_interp = interp1d(cr_values, baseline_data['ac_baseline'],
                               kind='linear', bounds_error=False, fill_value='extrapolate')
attack_baseline_interp = interp1d(cr_values, baseline_data['attack_baseline'],
                                   kind='linear', bounds_error=False, fill_value='extrapolate')
dpr_baseline_interp = interp1d(cr_values, baseline_data['dpr_baseline'],
                                kind='linear', bounds_error=False, fill_value='extrapolate')
dc_baseline_interp = interp1d(cr_values, baseline_data['dc_baseline'],
                               kind='linear', bounds_error=False, fill_value='extrapolate')

# Load monster data to find Owlbear
df = pd.read_csv('data/dnd5e_monsters_2014.csv')

# Find Owlbear
owlbear = df[df['Name'].str.lower() == 'owlbear'].iloc[0]

print("\n" + "=" * 80)
print("OWLBEAR STATS FROM DATASET")
print("=" * 80)
print(f"Name: {owlbear['Name']}")
print(f"CR: {owlbear['Challenge_Rating']}")
print(f"Actual HP: {owlbear['HP']}")
print(f"AC: {owlbear['AC']}")
print(f"Actions: {owlbear['Actions'][:200]}...")  # First 200 chars

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

cr = parse_cr(owlbear['Challenge_Rating'])

# Parse actual HP
def parse_hp(hp_str):
    if pd.isna(hp_str):
        return 0
    hp_str = str(hp_str).strip()
    match = re.match(r'(\d+)', hp_str)
    return int(match.group(1)) if match else 0

actual_hp = parse_hp(owlbear['HP'])

# Parse AC
def parse_ac(ac_str):
    if pd.isna(ac_str):
        return 10
    match = re.search(r'\d+', str(ac_str))
    return int(match.group()) if match else 10

ac_value = parse_ac(owlbear['AC'])

# Parse attack bonus
def parse_attack_bonus(actions_str):
    if pd.isna(actions_str):
        return 0
    matches = re.findall(r'\+(\d+)\s+to\s+hit', str(actions_str).lower())
    return max([int(m) for m in matches]) if matches else 0

attack_bonus = parse_attack_bonus(owlbear['Actions'])

# If attack bonus is 0 (data missing), estimate from CR
if attack_bonus == 0:
    # Typical owlbear has +7 to hit (based on standard 5e stats)
    attack_bonus = 7
    print("⚠️  Attack bonus not found in data, using typical CR 3 value: +7")

# Parse save DC
def parse_save_dc(text_str):
    if pd.isna(text_str):
        return 0
    matches = re.findall(r'dc\s+(\d+)', str(text_str).lower())
    return max([int(m) for m in matches]) if matches else 0

combined_text = str(owlbear['Traits']) + ' ' + str(owlbear['Actions']) + ' ' + str(owlbear['Reactions'])
save_dc = parse_save_dc(combined_text)

# Parse DPR (simplified - just get from dataset if available)
# For this test, we'll use a reasonable estimate for Owlbear
estimated_dpr = 28  # 2 × Rend attacks at 14 damage each

print("\n" + "=" * 80)
print("PARSED OWLBEAR STATS")
print("=" * 80)
print(f"CR: {cr}")
print(f"Actual HP: {actual_hp}")
print(f"AC: {ac_value}")
print(f"Attack Bonus: +{attack_bonus}")
print(f"Estimated DPR: {estimated_dpr}")
print(f"Save DC: {save_dc if save_dc > 0 else 'None'}")

# Select appropriate model
if cr <= 1.0:
    selected_model = model_low
    model_name = "Low-CR"
elif cr <= 12.0:
    selected_model = model_mid
    model_name = "Mid-CR"
else:
    selected_model = model_high
    model_name = "High-CR"

print(f"\n📊 Using {model_name} model (CR range: {selected_model['cr_range']})")

# PHASE 1: Get baselines
print("\n" + "=" * 80)
print("PHASE 1: CR BASELINE")
print("=" * 80)

hp_baseline = float(hp_baseline_interp(cr))
ac_baseline = float(ac_baseline_interp(cr))
attack_baseline = float(attack_baseline_interp(cr))
dpr_baseline = float(dpr_baseline_interp(cr))
dc_baseline = float(dc_baseline_interp(cr))

print(f"HP Baseline:     {hp_baseline:.1f}")
print(f"AC Baseline:     {ac_baseline:.1f}")
print(f"Attack Baseline: +{attack_baseline:.1f}")
print(f"DPR Baseline:    {dpr_baseline:.1f}")
print(f"DC Baseline:     {dc_baseline:.1f}")

phase1_hp = hp_baseline

# PHASE 2: Apply fixed penalties
print("\n" + "=" * 80)
print("PHASE 2: COMBAT STAT DEVIATIONS (FIXED PENALTIES)")
print("=" * 80)

ac_deviation = ac_value - ac_baseline
attack_deviation = attack_bonus - attack_baseline
dpr_deviation = estimated_dpr - dpr_baseline
save_dc_deviation = save_dc - dc_baseline if save_dc > 0 else 0

phase2_penalties = selected_model['phase2_penalties']

ac_penalty = ac_deviation * phase2_penalties['ac_deviation']
attack_penalty = attack_deviation * phase2_penalties['attack_deviation']
dpr_penalty = dpr_deviation * phase2_penalties['dpr_deviation']
save_dc_penalty = save_dc_deviation * phase2_penalties['save_dc_deviation']

print(f"AC Deviation:     {ac_deviation:+.1f} → {ac_penalty:+.1f} HP (penalty: {phase2_penalties['ac_deviation']:.1f} HP/point)")
print(f"Attack Deviation: {attack_deviation:+.1f} → {attack_penalty:+.1f} HP (penalty: {phase2_penalties['attack_deviation']:.1f} HP/point)")
print(f"DPR Deviation:    {dpr_deviation:+.1f} → {dpr_penalty:+.1f} HP (penalty: {phase2_penalties['dpr_deviation']:.1f} HP/point)")
print(f"Save DC Deviation:{save_dc_deviation:+.1f} → {save_dc_penalty:+.1f} HP (penalty: {phase2_penalties['save_dc_deviation']:.1f} HP/point)")

phase2_adjustment = ac_penalty + attack_penalty + dpr_penalty + save_dc_penalty
hp_after_phase2 = phase1_hp + phase2_adjustment

print(f"\nTotal Phase 2 Adjustment: {phase2_adjustment:+.1f} HP")
print(f"HP after Phase 2:         {hp_after_phase2:.1f} HP")

# PHASE 3: Predict residual from abilities
print("\n" + "=" * 80)
print("PHASE 3: RESIDUAL HP FROM ABILITIES")
print("=" * 80)

# For this example, assume Owlbear has no special abilities
# (In reality, you'd parse traits for flying, legendary resistance, etc.)
has_flying = 0
has_legendary_resistance = 0
has_magic_resistance = 0
has_regeneration = 0
has_legendary_actions = 0

# Build Phase 3 features
phase3_features = {}
for col in selected_model['feature_columns']:
    phase3_features[col] = 0

# Scaled features using hp_after_phase2
phase3_features['has_flying_scaled'] = has_flying * hp_after_phase2
phase3_features['has_legendary_resistance_scaled'] = has_legendary_resistance * hp_after_phase2
phase3_features['has_magic_resistance_scaled'] = has_magic_resistance * hp_after_phase2
phase3_features['has_regeneration_scaled'] = has_regeneration * hp_after_phase2
phase3_features['has_legendary_actions_scaled'] = has_legendary_actions * hp_after_phase2

# Set other features to reasonable defaults for Owlbear
phase3_features['size_ordinal'] = 3  # Large
phase3_features['speed_ground'] = 40
phase3_features['speed_fly'] = 0
phase3_features['max_speed'] = 40
phase3_features['movement_types_count'] = 1

print(f"Special Abilities:")
print(f"  - Flying: {has_flying}")
print(f"  - Legendary Resistance: {has_legendary_resistance}")
print(f"  - Magic Resistance: {has_magic_resistance}")
print(f"  - Regeneration: {has_regeneration}")
print(f"  - Legendary Actions: {has_legendary_actions}")

# Normalize features
X = []
for col in selected_model['feature_columns']:
    value = phase3_features.get(col, 0)
    mean = selected_model['scaler'].mean_[selected_model['feature_columns'].index(col)]
    scale = selected_model['scaler'].scale_[selected_model['feature_columns'].index(col)]
    X.append((value - mean) / scale)

X = np.array(X)

# Predict residual
residual_prediction = selected_model['intercept'] + np.dot(X, selected_model['coef'])

print(f"\nPredicted Residual HP: {residual_prediction:+.1f}")

# FINAL PREDICTION
print("\n" + "=" * 80)
print("FINAL PREDICTION")
print("=" * 80)

final_hp = hp_after_phase2 + residual_prediction

print(f"Phase 1 (Baseline):          {phase1_hp:>7.1f} HP")
print(f"Phase 2 (Combat Stats):      {phase2_adjustment:>+7.1f} HP")
print(f"Phase 3 (Abilities):         {residual_prediction:>+7.1f} HP")
print(f"─" * 40)
print(f"Predicted HP:                {final_hp:>7.1f} HP")
print(f"Actual HP:                   {actual_hp:>7.1f} HP")
print(f"Error:                       {final_hp - actual_hp:>+7.1f} HP ({100 * (final_hp - actual_hp) / actual_hp:+.1f}%)")

print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)
print(f"The Owlbear starts with {phase1_hp:.0f} HP from its CR {cr} baseline.")
print(f"After accounting for combat stats, it has {hp_after_phase2:.0f} HP.")
print(f"The model predicts {residual_prediction:+.0f} HP from other abilities,")
print(f"giving a final prediction of {final_hp:.0f} HP vs actual {actual_hp} HP.")
