"""
Baseline interpolation functions for the HP prediction model.

This module provides functions to interpolate baseline values (HP, AC, Attack, etc.)
for any CR value using the Lazy 5e reference data.
"""

import numpy as np
from scipy.interpolate import interp1d

from .feature_config import (
    BASELINE_DATA,
    FLY_SPEED_BASELINE,
    DARKVISION_BASELINE,
    GROUND_SPEED_BASELINE,
    get_cr_tier,
)


# =============================================================================
# CREATE INTERPOLATION FUNCTIONS
# =============================================================================

# Convert baseline data to numpy arrays for interpolation
_cr_values = np.array(BASELINE_DATA['cr_values'])
_hp_baseline = np.array(BASELINE_DATA['hp_baseline'])
_ac_baseline = np.array(BASELINE_DATA['ac_baseline'])
_attack_baseline = np.array(BASELINE_DATA['attack_baseline'])
_dpr_baseline = np.array(BASELINE_DATA['dpr_baseline'])
_size_ordinal_baseline = np.array(BASELINE_DATA['size_ordinal_baseline'])

# Create interpolation functions
_hp_baseline_interp = interp1d(
    _cr_values, _hp_baseline,
    kind='linear', bounds_error=False, fill_value='extrapolate'
)

_ac_baseline_interp = interp1d(
    _cr_values, _ac_baseline,
    kind='linear', bounds_error=False, fill_value='extrapolate'
)

_attack_baseline_interp = interp1d(
    _cr_values, _attack_baseline,
    kind='linear', bounds_error=False, fill_value='extrapolate'
)

_dpr_baseline_interp = interp1d(
    _cr_values, _dpr_baseline,
    kind='linear', bounds_error=False, fill_value='extrapolate'
)

# DC baseline uses same values as AC (from AC_DC column in Lazy 5e)
_dc_baseline_interp = interp1d(
    _cr_values, _ac_baseline,
    kind='linear', bounds_error=False, fill_value='extrapolate'
)

# Size ordinal uses step function (previous value)
_size_ordinal_baseline_interp = interp1d(
    _cr_values, _size_ordinal_baseline,
    kind='previous',  # Step function instead of linear
    bounds_error=False,
    fill_value=(2, 3)  # Medium below range, Large above range
)


# =============================================================================
# PUBLIC BASELINE FUNCTIONS
# =============================================================================

def get_baseline_hp(cr):
    """
    Get baseline HP for a given CR.

    The baseline HP is adjusted from Lazy 5e data:
    - +50% for CR <= 1
    - +20% for CR >= 2

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline HP value
    """
    return float(_hp_baseline_interp(cr))


def get_baseline_ac(cr):
    """
    Get baseline AC for a given CR.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline AC value
    """
    return float(_ac_baseline_interp(cr))


def get_baseline_attack(cr):
    """
    Get baseline attack bonus for a given CR.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline attack bonus
    """
    return float(_attack_baseline_interp(cr))


def get_baseline_dpr(cr):
    """
    Get baseline damage per round for a given CR.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline DPR
    """
    return float(_dpr_baseline_interp(cr))


def get_baseline_dc(cr):
    """
    Get baseline save DC for a given CR.

    Note: Uses same values as AC baseline (from Lazy 5e AC_DC column).

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline save DC
    """
    return float(_dc_baseline_interp(cr))


def get_baseline_size_ordinal(cr):
    """
    Get baseline size ordinal for a given CR.

    Size ordinals: 0=Tiny, 1=Small, 2=Medium, 3=Large, 4=Huge, 5=Gargantuan

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline size ordinal
    """
    return float(_size_ordinal_baseline_interp(cr))


def get_baseline_speed_ground(cr):
    """
    Get baseline ground speed for a given CR.

    Note: Ground speed baseline is constant at 30 ft for all CRs.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline ground speed (always 30.0)
    """
    return float(GROUND_SPEED_BASELINE)


def get_baseline_max_speed(cr):
    """
    Get baseline max speed for a given CR.

    Note: Max speed baseline is constant at 30 ft for all CRs
    (assumes ground speed as baseline maximum).

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        float: Baseline max speed (always 30.0)
    """
    return 30.0


def get_fly_speed_baseline(cr):
    """
    Get baseline fly speed for a given CR tier.

    Only applicable to creatures that can fly.
    Non-flying creatures should use 0 as their fly speed.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        int: Baseline fly speed in feet
    """
    tier = get_cr_tier(cr)
    return FLY_SPEED_BASELINE[tier]


def get_darkvision_baseline(cr):
    """
    Get baseline darkvision range for a given CR tier.

    Only applicable to creatures with darkvision.
    Creatures without darkvision should use 0.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        int: Baseline darkvision range in feet
    """
    tier = get_cr_tier(cr)
    return DARKVISION_BASELINE[tier]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_all_baselines(cr):
    """
    Get all baseline values for a given CR.

    Args:
        cr: Challenge Rating (numeric)

    Returns:
        dict: Dictionary with all baseline values
    """
    return {
        'hp_baseline': get_baseline_hp(cr),
        'ac_baseline': get_baseline_ac(cr),
        'attack_baseline': get_baseline_attack(cr),
        'dpr_baseline': get_baseline_dpr(cr),
        'dc_baseline': get_baseline_dc(cr),
        'size_ordinal_baseline': get_baseline_size_ordinal(cr),
        'speed_ground_baseline': get_baseline_speed_ground(cr),
        'fly_speed_baseline': get_fly_speed_baseline(cr),
        'darkvision_baseline': get_darkvision_baseline(cr),
    }


def calculate_deviations(row, baselines=None):
    """
    Calculate deviation features for a creature row.

    Args:
        row: DataFrame row or dict with creature stats
        baselines: Optional pre-computed baselines dict

    Returns:
        dict: Dictionary with deviation values
    """
    cr = row.get('cr_numeric', 0)

    if baselines is None:
        baselines = get_all_baselines(cr)

    deviations = {
        'ac_deviation': row.get('ac_value', 10) - baselines['ac_baseline'],
        'attack_deviation': row.get('highest_attack_bonus', 0) - baselines['attack_baseline'],
        'dpr_deviation': row.get('total_dpr', 0) - baselines['dpr_baseline'],
        'save_dc_deviation': row.get('highest_save_dc', 0) - baselines['dc_baseline'],
        'size_ordinal_deviation': row.get('size_ordinal', 2) - baselines['size_ordinal_baseline'],
        'speed_ground_deviation': row.get('speed_ground', 30) - baselines['speed_ground_baseline'],
    }

    # Fly speed deviation (only for flyers)
    if row.get('speed_fly', 0) > 0:
        deviations['speed_fly_deviation'] = row['speed_fly'] - baselines['fly_speed_baseline']
    else:
        deviations['speed_fly_deviation'] = 0

    # Darkvision deviation (only for creatures with darkvision)
    if row.get('darkvision_range', 0) > 0:
        deviations['darkvision_deviation'] = row['darkvision_range'] - baselines['darkvision_baseline']
    else:
        deviations['darkvision_deviation'] = 0

    return deviations
