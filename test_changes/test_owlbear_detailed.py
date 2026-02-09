#!/usr/bin/env python3
"""
Detailed breakdown of every feature's impact on Owlbear HP prediction.
Shows step-by-step calculation with all non-zero features.
"""

import pandas as pd
import numpy as np
import pickle
import json
from scipy.interpolate import interp1d
import re

print("=" * 80)
print("LOADING MODELS AND DATA")
print("=" * 80)

# Load models
with open('pickled_models/hp_model_mid_cr.pkl', 'rb') as f:
    model_mid = pickle.load(f)

# Load baseline data
with open('data/baseline_lookup_three_tier.json', 'r') as f:
    baseline_data = json.load(f)

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

# Load monster data
df = pd.read_csv('data/dnd5e_monsters_2014.csv')
owlbear = df[df['Name'].str.lower() == 'owlbear'].iloc[0]

# Parse functions
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

def parse_hp(hp_str):
    if pd.isna(hp_str):
        return 0
    match = re.match(r'(\d+)', str(hp_str).strip())
    return int(match.group(1)) if match else 0

def parse_ac(ac_str):
    if pd.isna(ac_str):
        return 10
    match = re.search(r'\d+', str(ac_str))
    return int(match.group()) if match else 10

# Parse Owlbear stats
cr = parse_cr(owlbear['Challenge_Rating'])
actual_hp = parse_hp(owlbear['HP'])
ac_value = parse_ac(owlbear['AC'])

# Estimate attack bonus (data is missing in CSV)
attack_bonus = 7  # Standard Owlbear value

# Estimate DPR: Owlbear makes 2 attacks, typical damage ~14 each
estimated_dpr = 28

save_dc = 0  # Owlbear has no save DC

print(f"Owlbear (CR {cr}):")
print(f"  Actual HP: {actual_hp}")
print(f"  AC: {ac_value}")
print(f"  Attack Bonus: +{attack_bonus}")
print(f"  DPR: {estimated_dpr}")
print(f"  Save DC: {save_dc if save_dc > 0 else 'None'}")

# ============================================================================
# PHASE 1: CR BASELINE
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 1: CR BASELINE")
print("=" * 80)

hp_baseline = float(hp_baseline_interp(cr))
ac_baseline = float(ac_baseline_interp(cr))
attack_baseline = float(attack_baseline_interp(cr))
dpr_baseline = float(dpr_baseline_interp(cr))
dc_baseline = float(dc_baseline_interp(cr))

print(f"\nBaselines for CR {cr}:")
print(f"  HP:     {hp_baseline:.1f}")
print(f"  AC:     {ac_baseline:.1f}")
print(f"  Attack: +{attack_baseline:.1f}")
print(f"  DPR:    {dpr_baseline:.1f}")
print(f"  DC:     {dc_baseline:.1f}")

phase1_hp = hp_baseline
print(f"\n→ Starting HP: {phase1_hp:.1f}")

# ============================================================================
# PHASE 2: COMBAT STAT DEVIATIONS (FIXED PENALTIES)
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 2: COMBAT STAT DEVIATIONS (FIXED PENALTIES)")
print("=" * 80)

phase2_penalties = model_mid['phase2_penalties']

# Calculate deviations
ac_deviation = ac_value - ac_baseline
attack_deviation = attack_bonus - attack_baseline
dpr_deviation = estimated_dpr - dpr_baseline
save_dc_deviation = save_dc - dc_baseline if save_dc > 0 else 0

# Calculate HP adjustments
ac_adjustment = ac_deviation * phase2_penalties['ac_deviation']
attack_adjustment = attack_deviation * phase2_penalties['attack_deviation']
dpr_adjustment = dpr_deviation * phase2_penalties['dpr_deviation']
save_dc_adjustment = save_dc_deviation * phase2_penalties['save_dc_deviation']

print(f"\nCombat Stat Deviations:")
print(f"  AC:     {ac_value} - {ac_baseline:.1f} = {ac_deviation:+.1f}")
print(f"          {ac_deviation:+.1f} × {phase2_penalties['ac_deviation']:.1f} HP/point = {ac_adjustment:+.1f} HP")
print()
print(f"  Attack: +{attack_bonus} - +{attack_baseline:.1f} = {attack_deviation:+.1f}")
print(f"          {attack_deviation:+.1f} × {phase2_penalties['attack_deviation']:.1f} HP/point = {attack_adjustment:+.1f} HP")
print()
print(f"  DPR:    {estimated_dpr} - {dpr_baseline:.1f} = {dpr_deviation:+.1f}")
print(f"          {dpr_deviation:+.1f} × {phase2_penalties['dpr_deviation']:.1f} HP/point = {dpr_adjustment:+.1f} HP")
print()
print(f"  Save DC: {save_dc if save_dc > 0 else 'None'} - {dc_baseline:.1f} = {save_dc_deviation:+.1f}")
print(f"          {save_dc_deviation:+.1f} × {phase2_penalties['save_dc_deviation']:.1f} HP/point = {save_dc_adjustment:+.1f} HP")

phase2_total = ac_adjustment + attack_adjustment + dpr_adjustment + save_dc_adjustment
hp_after_phase2 = phase1_hp + phase2_total

print(f"\n→ Phase 2 Total Adjustment: {phase2_total:+.1f} HP")
print(f"→ HP after Phase 2: {phase1_hp:.1f} + {phase2_total:+.1f} = {hp_after_phase2:.1f}")

# ============================================================================
# PHASE 3: BUILD FEATURE VECTOR
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 3: ABILITIES AND OTHER FEATURES")
print("=" * 80)

# Build feature vector (all features the model expects)
phase3_features = {}
for col in model_mid['feature_columns']:
    phase3_features[col] = 0

# Scaled abilities (using hp_after_phase2, not hp_baseline!)
phase3_features['has_flying_scaled'] = 0 * hp_after_phase2  # Owlbear doesn't fly
phase3_features['has_legendary_resistance_scaled'] = 0 * hp_after_phase2
phase3_features['has_magic_resistance_scaled'] = 0 * hp_after_phase2
phase3_features['has_regeneration_scaled'] = 0 * hp_after_phase2
phase3_features['has_legendary_actions_scaled'] = 0 * hp_after_phase2

# Movement
phase3_features['speed_ground'] = 40  # Owlbear speed
phase3_features['speed_fly'] = 0
phase3_features['speed_swim'] = 0
phase3_features['speed_burrow'] = 0
phase3_features['speed_climb'] = 40  # Owlbear can climb
phase3_features['max_speed'] = 40
phase3_features['movement_types_count'] = 2  # ground + climb

# Defenses (assuming typical Owlbear)
phase3_features['save_proficiency_count'] = 0
phase3_features['skill_proficiency_count'] = 1  # Perception
phase3_features['resistance_count'] = 0
phase3_features['immunity_count'] = 0
phase3_features['vulnerability_count'] = 0
phase3_features['condition_immunity_count'] = 0

# Senses
phase3_features['has_darkvision'] = 1  # Owlbear has darkvision
phase3_features['darkvision_range'] = 60
phase3_features['has_blindsight'] = 0
phase3_features['has_truesight'] = 0
phase3_features['has_tremorsense'] = 0
phase3_features['passive_perception'] = 13

# Abilities (Owlbear has keen sight/smell trait)
phase3_features['action_count'] = 3  # Multiattack, Beak, Claws
phase3_features['reaction_count'] = 0
phase3_features['bonus_action_count'] = 0
phase3_features['legendary_action_count'] = 0
phase3_features['legendary_actions_per_round'] = 0

# Other
phase3_features['has_spellcasting'] = 0
phase3_features['spellcaster_level'] = 0
phase3_features['size_ordinal'] = 3  # Large
phase3_features['has_grapple'] = 0

# Conditions (Owlbear doesn't inflict conditions)
for condition in ['poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
                  'incapacitated', 'paralyzed', 'petrified', 'prone', 'restrained', 'stunned']:
    phase3_features[f'inflicts_{condition}'] = 0

print(f"\nPhase 3 Feature Values (non-zero only):")
non_zero_features = {k: v for k, v in phase3_features.items() if v != 0}
for feat, value in sorted(non_zero_features.items()):
    print(f"  {feat:40s} = {value}")

# ============================================================================
# PHASE 3: PREDICT RESIDUAL HP
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 3: MODEL PREDICTION (FEATURE-BY-FEATURE)")
print("=" * 80)

# Normalize features and calculate contribution
print(f"\nModel Intercept: {model_mid['intercept']:.2f} HP")
residual_prediction = model_mid['intercept']

feature_contributions = []

for i, col in enumerate(model_mid['feature_columns']):
    value = phase3_features[col]
    mean = model_mid['scaler'].mean_[i]
    scale = model_mid['scaler'].scale_[i]
    coef = model_mid['coef'][i]

    # Standardize
    standardized = (value - mean) / scale

    # Calculate contribution
    contribution = standardized * coef

    # Only show non-zero or significant contributions
    if abs(contribution) > 0.1 or value != 0:
        feature_contributions.append((col, value, mean, scale, standardized, coef, contribution))

print(f"\nFeature Contributions (showing features with |contribution| > 0.1 or non-zero value):")
print(f"{'Feature':<40} {'Value':>8} {'Mean':>8} {'Std Val':>8} {'Coef':>10} {'Contrib':>10}")
print("-" * 100)

for col, value, mean, scale, standardized, coef, contribution in sorted(feature_contributions, key=lambda x: abs(x[6]), reverse=True):
    print(f"{col:<40} {value:8.2f} {mean:8.2f} {standardized:8.2f} {coef:10.2f} {contribution:10.2f}")
    residual_prediction += contribution

print("-" * 100)
print(f"{'TOTAL RESIDUAL PREDICTION':<40} {'':8} {'':8} {'':8} {'':10} {residual_prediction:10.2f}")

# ============================================================================
# FINAL RESULT
# ============================================================================
print("\n" + "=" * 80)
print("FINAL HP CALCULATION")
print("=" * 80)

final_hp = hp_after_phase2 + residual_prediction

print(f"\nStep-by-step breakdown:")
print(f"  1. Phase 1 (CR {cr} baseline):      {phase1_hp:>8.1f} HP")
print(f"  2. Phase 2 (combat stats):         {phase2_total:>+8.1f} HP")
print(f"     → HP after Phase 2:             {hp_after_phase2:>8.1f} HP")
print(f"  3. Phase 3 (abilities):            {residual_prediction:>+8.1f} HP")
print(f"     ───────────────────────────────────────────")
print(f"     PREDICTED HP:                   {final_hp:>8.1f} HP")
print(f"     ACTUAL HP:                      {actual_hp:>8.1f} HP")
print(f"     ERROR:                          {final_hp - actual_hp:>+8.1f} HP ({100 * (final_hp - actual_hp) / actual_hp:+.1f}%)")

print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)
print(f"""
The Owlbear's HP is calculated as:
  • Starts with {phase1_hp:.0f} HP (CR {cr} baseline from Lazy 5e × 1.2)
  • Combat stats give {phase2_total:+.0f} HP:
    - AC is at baseline ({ac_value} vs {ac_baseline:.0f}): {ac_adjustment:+.0f} HP
    - Attack is +{attack_deviation:.0f} above baseline: {attack_adjustment:+.0f} HP
    - DPR is +{dpr_deviation:.0f} above baseline: {dpr_adjustment:+.0f} HP
  • After Phase 2: {hp_after_phase2:.0f} HP
  • Phase 3 predicts {residual_prediction:+.0f} HP from abilities
  • Final prediction: {final_hp:.0f} HP (actual: {actual_hp} HP)

Error: {final_hp - actual_hp:+.0f} HP ({100 * (final_hp - actual_hp) / actual_hp:+.1f}%)
""")

# Show which features are driving the large residual
print("Features with largest impact on Phase 3 residual:")
top_features = sorted(feature_contributions, key=lambda x: abs(x[6]), reverse=True)[:10]
for col, value, mean, scale, standardized, coef, contribution in top_features:
    print(f"  {col:<40} {contribution:>+8.2f} HP")
