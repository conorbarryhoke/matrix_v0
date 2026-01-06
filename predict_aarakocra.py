#!/usr/bin/env python3
"""
Predict HP for an Aarakocra using the constrained conditions model
"""

import pickle
import numpy as np

# Define the custom model class (needed for unpickling)
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

# Load the model artifacts
with open('pickled_models/hp_lr_model_with_conditions.pkl', 'rb') as f:
    model = pickle.load(f)

with open('pickled_models/hp_scaler_with_conditions.pkl', 'rb') as f:
    scaler = pickle.load(f)

with open('pickled_models/hp_feature_columns_with_conditions.pkl', 'rb') as f:
    feature_columns = pickle.load(f)

print("=" * 70)
print("AARAKOCRA HP PREDICTION")
print("=" * 70)

# Initialize all features to 0
features = {feat: 0 for feat in feature_columns}

# Aarakocra characteristics from Monster Manual
print("\n📋 AARAKOCRA STATS (Monster Manual):")
print("   - CR: 1/4 (0.25)")
print("   - AC: 12")
print("   - Speed: 20 ft walk, 50 ft fly")
print("   - Attack: Talon +4 to hit, 1d4+2 (avg 4 damage)")
print("   - Attack: Javelin +4 to hit, 1d6+2 (avg 5 damage)")
print("   - DPR: ~4.5 damage per round")
print("   - Size: Medium")
print("   - Type: Humanoid")
print("   - Actual HP: 13 (3d8)")

# Core features
features['cr_numeric'] = 0.25
features['ac_value'] = 12
features['size_ordinal'] = 2  # Medium

# Speed features
features['speed_ground'] = 20
features['speed_fly'] = 50
features['speed_swim'] = 0
features['speed_burrow'] = 0
features['speed_climb'] = 0
features['max_speed'] = 50
features['movement_types_count'] = 2  # walk + fly
features['has_flying'] = 1  # KEY FEATURE: Flying creature

# Combat features
features['highest_attack_bonus'] = 4
features['highest_save_dc'] = 0  # No save DC
features['estimated_dpr'] = 4.5  # Average between talon and javelin
features['has_multiattack'] = 0

# Defensive features
features['resistance_count'] = 0
features['immunity_count'] = 0
features['vulnerability_count'] = 0
features['condition_immunity_count'] = 0

# Special abilities
features['has_legendary_actions'] = 0
features['legendary_action_count'] = 0
features['legendary_actions_per_round'] = 0
features['has_legendary_resistance'] = 0
features['has_magic_resistance'] = 0
features['has_regeneration'] = 0
features['has_spellcasting'] = 0
features['spellcaster_level'] = 0
features['has_grapple'] = 0

# Senses (Aarakocra have keen eyesight)
features['has_darkvision'] = 0
features['darkvision_range'] = 0
features['has_blindsight'] = 0
features['has_truesight'] = 0
features['has_tremorsense'] = 0
features['passive_perception'] = 14  # Perception +2, WIS +2

# Proficiencies
features['save_proficiency_count'] = 0
features['skill_proficiency_count'] = 1  # Perception

# Action economy
features['trait_count'] = 1  # Dive Attack trait
features['action_count'] = 2  # Talon + Javelin
features['reaction_count'] = 0
features['bonus_action_count'] = 0
features['total_ability_count'] = 3

# Conditions (Aarakocra don't inflict conditions)
features['inflicts_poisoned'] = 0
features['inflicts_blinded'] = 0
features['inflicts_charmed'] = 0
features['inflicts_deafened'] = 0
features['inflicts_frightened'] = 0
features['inflicts_incapacitated'] = 0
features['inflicts_paralyzed'] = 0
features['inflicts_petrified'] = 0
features['inflicts_prone'] = 0
features['inflicts_restrained'] = 0
features['inflicts_stunned'] = 0

# Type: Humanoid
features['type_humanoid'] = 1

# Convert to feature vector in correct order
X = np.array([[features[feat] for feat in feature_columns]])

# Scale and predict
X_scaled = scaler.transform(X)
predicted_hp = model.predict(X_scaled)[0]

print(f"\n🔮 MODEL PREDICTION:")
print(f"   Predicted HP: {predicted_hp:.1f}")
print(f"   Actual HP: 13")
print(f"   Difference: {predicted_hp - 13:.1f} HP ({(predicted_hp - 13) / 13 * 100:+.1f}%)")

print(f"\n💡 KEY COEFFICIENT IMPACTS:")
print(f"   - CR 0.25 base contribution")
print(f"   - AC 12: -5 HP per point = -60 HP total")
print(f"   - Attack +4: -6 HP per point = -24 HP total")
print(f"   - DPR 4.5: -2.5 HP per point = -11.25 HP total")
print(f"   - Has Flying: -7 HP (major penalty)")

print(f"\n📊 ANALYSIS:")
if abs(predicted_hp - 13) < 5:
    print("   ✅ Excellent prediction! Model is very accurate.")
elif abs(predicted_hp - 13) < 10:
    print("   ✓ Good prediction within acceptable range.")
else:
    print("   ⚠️ Prediction differs significantly from actual.")

print(f"\n   The Aarakocra is a low-CR flying creature with:")
print(f"   - Mobility advantage (fly 50 ft) penalized by has_flying=-7")
print(f"   - Low offensive power (DPR 4.5)")
print(f"   - Low defenses (AC 12, no resistances)")
print(f"   - This balances to a fragile skirmisher archetype")

print("\n" + "=" * 70)
