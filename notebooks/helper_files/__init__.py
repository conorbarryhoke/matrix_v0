"""
Helper files for the HP prediction model.

This package contains modularized components extracted from the
three_tier_hp_model_merged.ipynb notebook:

- feature_config: Constants, feature lists, penalty configurations
- parsers: Functions to parse raw creature data into numeric features
- baseline_functions: CR-based baseline interpolation functions
- model_utils: Model training, evaluation, and analysis helpers
"""

from .feature_config import (
    CR_TIERS,
    CONDITIONS,
    PHASE2_FEATURES,
    PHASE2_PENALTIES,
    PHASE3_FEATURES_BASE,
    BASELINE_DATA,
    FLY_SPEED_BASELINE,
    DARKVISION_BASELINE,
    GROUND_SPEED_BASELINE,
    RESISTANCE_PENALTY_PER_COUNT,
    IMMUNITY_PENALTY_PER_COUNT,
    MODEL_CONFIG,
    EXPORT_COLUMNS,
    get_cr_tier,
    get_phase3_features,
    get_export_columns,
)

from .baseline_functions import (
    get_baseline_hp,
    get_baseline_ac,
    get_baseline_attack,
    get_baseline_dpr,
    get_baseline_dc,
    get_baseline_size_ordinal,
    get_baseline_speed_ground,
    get_baseline_max_speed,
    get_fly_speed_baseline,
    get_darkvision_baseline,
    get_all_baselines,
    calculate_deviations,
)

from .parsers import (
    parse_cr,
    parse_hp,
    parse_hp_avg,
    parse_bonus,
    adjust_hp_baseline,
    parse_ac,
    parse_speed,
    SIZE_ORDINAL_MAP,
    parse_size_ordinal,
    count_proficiencies,
    has_sense,
    parse_sense_range,
    parse_passive_perception,
    count_abilities,
    parse_legendary_actions,
    parse_attack_bonus,
    parse_save_dc,
    calculate_average_damage,
    parse_dpr_from_json,
    parse_charge_bonus_attack,
    parse_legendary_actions_dpr,
    parse_legendary_conditions,
    extract_spellcaster_level,
    has_advantage_condition,
    has_disadvantage_condition,
    has_attackers_advantage,
    get_resistance_multiplier,
    get_immunity_multiplier,
    extract_family,
)

from .model_utils import (
    BOOLEAN_FEATURES_BASE,
    get_boolean_features,
    train_constrained_model,
    train_unconstrained_model,
    ConstrainedModel,
    get_prediction,
    add_percentile_by_cr,
    calculate_r2,
    calculate_mae,
    calculate_mape,
    evaluate_model,
    save_model,
    load_model,
    log_model_performance,
)

from .model_analysis import (
    investigate_creature,
    summarize_model_performance,
    analyze_predictions_by_cr,
    plot_performance_scatter,
    plot_error_hist
)

__version__ = '1.0.0'
