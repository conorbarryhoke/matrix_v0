"""
Feature configuration for the HP prediction model.

This module contains all constants, feature lists, and penalty configurations
used across the feature engineering, model training, and analysis notebooks.
"""

# =============================================================================
# CR TIER BOUNDARIES
# =============================================================================
# Each tier has its own model with tier-specific penalties

CR_TIERS = {
    'cr1': {'min': 0, 'max': 1, 'exclusive_max': True, 'label': 'CR < 1'},
    'cr2': {'min': 1, 'max': 4, 'exclusive_max': False, 'label': 'CR 1-4'},
    'cr3': {'min': 5, 'max': 10, 'exclusive_max': False, 'label': 'CR 5-10'},
    'cr4': {'min': 11, 'max': 16, 'exclusive_max': False, 'label': 'CR 11-16'},
    'cr5': {'min': 17, 'max': float('inf'), 'exclusive_max': False, 'label': 'CR > 16'},
}

def get_cr_tier(cr):
    """Return the tier key (cr1-cr5) for a given CR value."""
    if cr < 1:
        return 'cr1'
    elif cr <= 4:
        return 'cr2'
    elif cr <= 10:
        return 'cr3'
    elif cr <= 16:
        return 'cr4'
    else:
        return 'cr5'


# =============================================================================
# CONDITION DEFINITIONS
# =============================================================================
# Conditions that can be inflicted by creature abilities

CONDITIONS = [
    'poisoned', 'blinded', 'charmed', 'deafened', 'frightened',
    'incapacitated', 'paralyzed', 'petrified', 'restrained', 'stunned'
]


# =============================================================================
# PHASE 2 FEATURES (FIXED PENALTIES)
# =============================================================================
# These features have manually-tuned penalties that scale with CR

PHASE2_FEATURES = [
    'ac_deviation',
    'attack_deviation',
    'dpr_deviation',
    'save_dc_deviation',
    'has_flying',
    'has_advantage_condition',
    'has_disadvantage_condition',
    'has_attackers_advantage',
    'inflicts_prone',
]

# Phase 2 penalties by CR tier
# Positive penalty = reduces HP (offensive feature)
# Negative penalty = increases HP (defensive feature)

PHASE2_PENALTIES = {
    'cr1': {
        'ac_deviation': -1.5,
        'attack_deviation': -2.0,
        'dpr_deviation': -0.75,
        'save_dc_deviation': -3.5,
        'has_flying': -2.5,  # Fixed penalty for flying
        'has_advantage_condition': -1.5,  # 0.75 * attack_deviation
        'has_disadvantage_condition': 1.0,  # -0.5 * attack_deviation (adds HP)
        'has_attackers_advantage': 3.0,  # -0.5 * 4 * ac_deviation (adds HP)
        'inflicts_prone': -0.75,  # 0.75 * 0.5 * attack_deviation (with save)
    },
    'cr2': {
        'ac_deviation': -2.5,
        'attack_deviation': -3.0,
        'dpr_deviation': -1.0,
        'save_dc_deviation': -5.0,
        'has_flying': -4.0,
        'has_advantage_condition': -2.25,
        'has_disadvantage_condition': 1.5,
        'has_attackers_advantage': 5.0,
        'inflicts_prone': -1.125,
    },
    'cr3': {
        'ac_deviation': -3.5,
        'attack_deviation': -4.0,
        'dpr_deviation': -1.25,
        'save_dc_deviation': -6.0,
        'has_flying': -5.0,
        'has_advantage_condition': -3.0,
        'has_disadvantage_condition': 2.0,
        'has_attackers_advantage': 7.0,
        'inflicts_prone': -1.5,
    },
    'cr4': {
        'ac_deviation': -4.5,
        'attack_deviation': -5.0,
        'dpr_deviation': -1.5,
        'save_dc_deviation': -7.5,
        'has_flying': -6.0,
        'has_advantage_condition': -3.75,
        'has_disadvantage_condition': 2.5,
        'has_attackers_advantage': 9.0,
        'inflicts_prone': -1.875,
    },
    'cr5': {
        'ac_deviation': -6.0,
        'attack_deviation': -6.5,
        'dpr_deviation': -2.0,
        'save_dc_deviation': -9.0,
        'has_flying': -7.5,
        'has_advantage_condition': -4.875,
        'has_disadvantage_condition': 3.25,
        'has_attackers_advantage': 12.0,
        'inflicts_prone': -2.4375,
    },
}


# =============================================================================
# PHASE 3 FEATURES (LEARNED COEFFICIENTS)
# =============================================================================
# These features have coefficients learned via constrained regression

PHASE3_FEATURES_BASE = [
    'has_legendary_resistance_scaled',
    'has_magic_resistance_scaled',
    'has_regeneration_scaled',
    'speed_ground_deviation', 'speed_fly_deviation', 'speed_swim', 'speed_burrow', 'speed_climb',
    'movement_types_count',
    'save_proficiency_count', 'skill_proficiency_count',
    'vulnerability_count', 'condition_immunity_count',
    'has_darkvision', 'darkvision_deviation', 'has_blindsight', 'has_truesight', 'has_tremorsense',
    'trait_count', 'reaction_count', 'bonus_action_count',
    'legendary_action_count', 'legendary_actions_per_round',
    'total_ability_count',
    'has_spellcasting', 'spellcaster_level',
    'size_ordinal_deviation', 'has_grapple'
]

# Full Phase 3 features including condition infliction
def get_phase3_features():
    """Return the full list of Phase 3 features including condition features."""
    features = PHASE3_FEATURES_BASE.copy()
    for condition in CONDITIONS:
        features.append(f'inflicts_{condition}')
    return features


# =============================================================================
# BASELINE DATA
# =============================================================================
# Reference data points for interpolation (from Lazy 5e stats)

BASELINE_DATA = {
    'cr_values': [0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0,
                  12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0],
    'hp_baseline': [4.5, 13.5, 19.5, 33.0, 49.5, 54.0, 78.0, 100.8, 114.0, 134.4, 156.0, 163.2, 174.0, 186.0, 198.0,
                    210.0, 222.0, 234.0, 246.0, 258.0, 270.0, 282.0, 294.0, 306.0, 318.0, 330.0, 342.0, 354.0, 366.0, 378.0, 390.0, 402.0, 414.0, 426.0],
    'ac_baseline': [10, 11, 11, 12, 12, 13, 13, 14, 15, 15, 15, 15, 16, 17, 17,
                    17, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19, 19],
    'attack_baseline': [2, 3, 3, 4, 5, 5, 5, 6, 7, 7, 7, 7, 8, 9, 9,
                        9, 10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 13, 13, 13, 14, 14, 14, 14],
    'dpr_baseline': [2, 3, 5, 8, 12, 17, 23, 28, 35, 41, 47, 53, 59, 65, 71,
                     77, 83, 89, 95, 101, 107, 113, 119, 125, 131, 137, 143, 149, 155, 161, 167, 173, 179, 185],
    'size_ordinal_baseline': [2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3,
                              3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
}


# =============================================================================
# SPEED BASELINES BY CR TIER
# =============================================================================

FLY_SPEED_BASELINE = {
    'cr1': 30,   # CR < 1: min is 30, mode is 60, use min as baseline
    'cr2': 40,   # CR 1-4: min is 40, mode is 60
    'cr3': 60,   # CR 5-10: mode shifts to 80, baseline at 60
    'cr4': 60,   # CR 11-16: mode is 80, baseline at 60
    'cr5': 60,   # CR > 16: min is 60, mode is 80
}

DARKVISION_BASELINE = {
    'cr1': 60,   # CR < 1: mode is 60
    'cr2': 60,   # CR 1-4: mode is 60
    'cr3': 60,   # CR 5-10: mode is 60
    'cr4': 120,  # CR 11-16: mode shifts to 120
    'cr5': 120,  # CR > 16: all are 120
}

# Ground speed baseline is constant
GROUND_SPEED_BASELINE = 30


# =============================================================================
# PHASE 1.5 RESISTANCE/IMMUNITY PENALTIES
# =============================================================================
# These penalties are applied based on count of resistances/immunities

RESISTANCE_PENALTY_PER_COUNT = 0.025  # 2.5% HP reduction per resistance
IMMUNITY_PENALTY_PER_COUNT = 0.05     # 5% HP reduction per immunity


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# Settings for the constrained regression model

MODEL_CONFIG = {
    # Boolean features must have non-positive coefficients (reduce HP)
    'constrained_features': [
        'has_legendary_resistance_scaled',
        'has_magic_resistance_scaled',
        'has_regeneration_scaled',
        'has_darkvision',
        'has_blindsight',
        'has_truesight',
        'has_tremorsense',
        'has_spellcasting',
        'has_grapple',
    ],
    # Minimum R² to consider a model acceptable
    'min_r2': 0.6,
    # Maximum allowed coefficient magnitude for stability
    'max_coef_magnitude': 50.0,
}


# =============================================================================
# EXPORT COLUMNS
# =============================================================================
# Columns to include in exported prediction data

EXPORT_COLUMNS = [
    # Identifiers
    'Name', 'cr_numeric', 'actual_hp',

    # Predictions
    'predicted_hp', 'hp_delta', 'hp_delta_pct', 'hp_delta_pct_percentile',

    # Baselines
    'hp_baseline', 'ac_baseline', 'attack_baseline', 'dpr_baseline', 'dc_baseline',

    # Combat stats
    'highest_attack_bonus', 'highest_save_dc', 'estimated_dpr', 'legendary_dpr', 'total_dpr',

    # Phase 2: Deviations
    'ac_deviation', 'attack_deviation', 'dpr_deviation', 'save_dc_deviation',

    # Phase intermediates
    'hp_after_phase1_5', 'hp_after_phase2', 'residual_hp',

    # Phase 3: Scaled features
    'has_legendary_resistance_scaled',
    'has_magic_resistance_scaled', 'has_regeneration_scaled',

    # Phase 3: Movement
    'speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb',
    'max_speed', 'movement_types_count', 'has_flying',

    # Phase 3: Defenses
    'save_proficiency_count', 'skill_proficiency_count',
    'resistance_count', 'immunity_count', 'vulnerability_count',
    'condition_immunity_count',

    # Phase 3: Senses
    'has_darkvision', 'darkvision_deviation', 'has_blindsight',
    'has_truesight', 'has_tremorsense', 'passive_perception',

    # Phase 3: Abilities
    'trait_count', 'action_count', 'reaction_count', 'bonus_action_count',
    'legendary_action_count', 'legendary_actions_per_round',
    'total_ability_count',

    # Phase 3: Spellcasting
    'has_spellcasting', 'spellcaster_level',

    # Phase 3: Size
    'size_ordinal', 'size_ordinal_baseline', 'size_ordinal_deviation',

    # Condition inflictions (added dynamically)
]

def get_export_columns():
    """Return the full list of export columns including condition features."""
    cols = EXPORT_COLUMNS.copy()
    for condition in CONDITIONS:
        cols.append(f'inflicts_{condition}')
    return cols
