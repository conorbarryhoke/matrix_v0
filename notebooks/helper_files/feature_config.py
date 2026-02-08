"""
Feature configuration for the HP prediction model.

This module contains all constants, feature lists, and penalty configurations
used across the feature engineering, model training, and analysis notebooks.
"""

# =============================================================================
# COMBAT ASSUMPTIONS
# =============================================================================

EXPECTED_COMBAT_ROUNDS = 3  # DMG assumes 3-round combat for CR calculation


# =============================================================================
# DMG MONSTER FEATURE NAMES
# =============================================================================
# Complete list of DMG Monster Features (pp.280-281), one per CSV row in
# data/dmg_monster_feature_costs.csv. Each generates a feature_{name} column.
# "Undead Fortitude" is merged into "relentless" (both = "don't die at 0 HP").
# claude: 92 entries (93 CSV rows minus the Undead Fortitude merge).
#   To add a new DMG feature: add here, add detection in parsers.py → parse_dmg_features(),
#   and optionally add AC/attack cost to DMG_AC_ADJUSTMENTS / DMG_ATTACK_ADJUSTMENTS below.

DMG_FEATURE_NAMES = [
    'aggressive', 'ambusher', 'amorphous', 'amphibious', 'angelic_weapons',
    'antimagic_susceptibility', 'avoidance', 'blind_senses', 'blood_frenzy',
    'breath_weapon', 'brute', 'charge', 'charm', 'constrict',
    'damage_absorption', 'damage_transfer', 'death_burst', 'devils_sight',
    'dive_attack', 'echolocation', 'elemental_body', 'enlarge',
    'etherealness', 'false_appearance', 'fey_ancestry', 'fiendish_blessing',
    'flyby', 'frightful_presence', 'grapple', 'grappler', 'hold_breath',
    'horrifying_visage', 'illumination', 'immutable_form',
    'incorporeal_movement', 'innate_spellcasting', 'invisibility',
    'keen_senses', 'labyrinthine_recall', 'leadership',
    'legendary_resistance', 'life_drain', 'light_sensitivity',
    'magic_resistance', 'magic_weapons', 'martial_advantage', 'mimicry',
    'nightmare_haunting', 'nimble_escape', 'otherworldly_perception',
    'pack_tactics', 'parry', 'possession', 'pounce', 'prone', 'psychic_defense',
    'rampage', 'read_thoughts', 'reckless', 'redirect_attack', 'reel',
    'regeneration', 'rejuvenation', 'relentless', 'shadow_stealth',
    'shapechange', 'siege_monster', 'slippery', 'sneak_attack',
    'spell_immunity', 'spellcasting', 'spider_climb', 'standing_leap',
    'steadfast', 'stench', 'sunlight_sensitivity', 'superior_invisibility',
    'sure_footed', 'surprise_attack', 'swallow', 'teleport',
    'terrain_camouflage', 'threatening_reach', 'tunneler', 'turn_immunity',
    'turn_resistance', 'two_heads', 'web', 'web_sense', 'web_walker',
    'wounded_fury',
]


# =============================================================================
# DMG MONSTER FEATURE COSTS
# =============================================================================
# From DMG pp.280-281 "Monster Features" table.
# These adjust a monster's effective AC or attack bonus for CR purposes.
# Keys are lowercase trait/action names matched against creature data.
# Only features with quantified AC/attack costs are listed here.

DMG_AC_ADJUSTMENTS = {
    'magic resistance': 2,
    'shadow stealth': 4,
    'stench': 1,
    'invisibility': 1,
    'nimble escape': 4,
    'constrict': 1,
    'web': 1,
    'avoidance': 1,
    'parry': 1,
    'superior invisibility': 2,
}

DMG_ATTACK_ADJUSTMENTS = {
    'pack tactics': 1,
    'blood frenzy': 4,
    'ambusher': 1,
    'nimble escape': 4,
    'prone': 2,
}

# Fixed per-round DPR adjustments from DMG features
# Keys use snake_case feature names (matched against feature_{name} columns).
DMG_DPR_ADJUSTMENTS = {
    'aggressive': 2,     # "Increase effective per-round damage output by 2"
    'rampage': 2,        # "Increase effective per-round damage output by 2"
}

# =============================================================================
# DMG HP ADJUSTMENTS
# =============================================================================
# From DMG pp.280-281. Features that increase a monster's effective hit points.
# Applied as feature_hp in the 4-layer convention (hp_baseline + feature_hp = hp_after_phase1).

# Per-use HP bonus by CR tier — multiply by number of uses (parsed from trait Desc)
DMG_HP_PER_USE = {
    'legendary_resistance': {'cr1': 0, 'cr2': 10, 'cr3': 20, 'cr4': 30, 'cr5': 40},
}

# Fixed HP bonus by CR tier
DMG_HP_BY_TIER = {
    'relentless': {'cr1': 0, 'cr2': 7, 'cr3': 14, 'cr4': 21, 'cr5': 28},
}

# Percentage of hp_baseline added as bonus (only applied when CR ≤ 10)
DMG_HP_PERCENTAGE = {
    'frightful_presence': 0.25,   # +25% HP if facing characters level ≤ 10
    'horrifying_visage': 0.25,    # "See Frightful Presence" per DMG
}

# HP multiplier — effective HP is multiplied by this value.
# feature_hp = hp_baseline × (multiplier - 1) so it adds the EXTRA, not the total.
DMG_HP_MULTIPLIER = {
    'possession': 2.0,       # "Double the monster's effective hit points"
    'damage_transfer': 2.0,  # "Double the monster's effective hit points"
}

# Features that override has_advantage_condition when detected (known cost)
DMG_ADVANTAGE_OVERRIDES = [
    'pack_tactics', 'blood_frenzy', 'ambusher', 'reckless', 'grappler',
]

# Features that override has_attackers_advantage when detected (known cost)
DMG_ATTACKERS_ADVANTAGE_OVERRIDES = [
    'reckless',
]

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
    'has_regeneration_scaled',
    'vulnerability_count',
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
        'has_regeneration_scaled',
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

    # Combat stats (4-layer: estimated + feature + legendary = total)
    'highest_attack_bonus', 'highest_save_dc',
    'estimated_dpr', 'feature_dpr', 'legendary_dpr', 'total_dpr',
    'feature_ac', 'total_ac',
    'feature_attack', 'total_attack',

    # HP cost layer — DMG-specified HP adjustments
    'feature_hp',

    # DMG feature flags — added dynamically from DMG_FEATURE_NAMES in get_export_columns()

    # Phase 2: Deviations
    'ac_deviation', 'attack_deviation', 'dpr_deviation', 'save_dc_deviation',

    # Phase intermediates
    'hp_after_phase2', 'hp_after_resist_immun_penalty', 'residual_hp',

    # Phase 3: Scaled features
    'has_legendary_resistance_scaled', 'has_regeneration_scaled',

    # Movement (informational — has_flying feeds into feature_ac for CR ≤ 10)
    'has_flying',

    # Defenses
    'save_proficiency_count',
    'resistance_count', 'immunity_count', 'vulnerability_count',

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
    """Return the full list of export columns including DMG features and condition features."""
    cols = EXPORT_COLUMNS.copy()
    # DMG feature flags (92 columns from DMG_FEATURE_NAMES)
    for name in DMG_FEATURE_NAMES:
        cols.append(f'feature_{name}')
    # Condition infliction flags (auto-generated from CONDITIONS)
    for condition in CONDITIONS:
        cols.append(f'inflicts_{condition}')
    return cols
