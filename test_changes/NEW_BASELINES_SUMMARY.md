# New Baselines Implementation Summary

## Overview

Added three new baseline-deviation features to the HP model:
- `size_ordinal_deviation` - measures if creature is larger/smaller than expected for CR
- `speed_ground_deviation` - measures if creature is faster/slower than standard 30ft
- `max_speed_deviation` - measures if creature's max speed exceeds standard 30ft

## Changes Made

### 1. Updated `three_tier_hp_model.ipynb`

#### Cell 6: Added baseline columns to lazy_5e dataframe
```python
# Add size_ordinal baseline (Medium for CR < 12, Large for CR >= 12)
lazy_5e['size_ordinal_baseline'] = lazy_5e['cr_numeric'].apply(
    lambda cr: 2 if cr < 12 else 3  # 2 = Medium, 3 = Large
)

# Add speed baselines (constant 30 for all CR)
lazy_5e['speed_ground_baseline'] = 30
lazy_5e['max_speed_baseline'] = 30
```

#### Cell 7: Added interpolation functions
```python
# Size ordinal baseline (step function at CR 12)
size_ordinal_baseline_interp = interp1d(
    cr_values,
    lazy_5e['size_ordinal_baseline'].values,
    kind='previous',  # Use step function instead of linear
    bounds_error=False,
    fill_value=(2, 3)  # Medium below range, Large above range
)

def get_baseline_size_ordinal(cr):
    return float(size_ordinal_baseline_interp(cr))

# Speed baselines (constant functions)
def get_baseline_speed_ground(cr):
    return 30.0

def get_baseline_max_speed(cr):
    return 30.0
```

#### Cell 15: Added baseline and deviation calculations
```python
# Add baseline values
df['size_ordinal_baseline'] = df['cr_numeric'].apply(get_baseline_size_ordinal)
df['speed_ground_baseline'] = df['cr_numeric'].apply(get_baseline_speed_ground)
df['max_speed_baseline'] = df['cr_numeric'].apply(get_baseline_max_speed)

# Calculate deviations
df['size_ordinal_deviation'] = df['size_ordinal'] - df['size_ordinal_baseline']
df['speed_ground_deviation'] = df['speed_ground'] - df['speed_ground_baseline']
df['max_speed_deviation'] = df['max_speed'] - df['max_speed_baseline']
```

#### Cell 16: Updated phase3_features list
Changed from raw values to deviations:
```python
phase3_features = [
    ...,
    'speed_ground_deviation',    # CHANGED from 'speed_ground'
    'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb',
    'max_speed_deviation',       # CHANGED from 'max_speed'
    'movement_types_count',
    ...,
    'size_ordinal_deviation',    # CHANGED from 'size_ordinal'
    'has_grapple'
]
```

### 2. Updated `baseline_lookup_three_tier.json`

Added three new arrays:
- `size_ordinal_baseline`: [2, 2, 2, ..., 2, 3, 3, ...] (34 values)
- `speed_ground_baseline`: [30, 30, 30, ..., 30] (34 values)
- `max_speed_baseline`: [30, 30, 30, ..., 30] (34 values)

## Interpretation

### Size Ordinal Deviation
- **Positive value**: Creature is larger than expected for its CR
  - Example: CR 5 Huge creature → baseline=2 (Medium), actual=4 (Huge) → deviation=+2
- **Zero**: Creature is the expected size
  - Example: CR 5 Medium creature → baseline=2, actual=2 → deviation=0
- **Negative value**: Creature is smaller than expected
  - Example: CR 15 Small creature → baseline=3 (Large), actual=1 (Small) → deviation=-2

### Speed Ground Deviation
- **Positive value**: Creature is faster than standard 30ft
  - Example: Speed 40 → deviation=+10
- **Zero**: Standard speed
  - Example: Speed 30 → deviation=0
- **Negative value**: Creature is slower than standard
  - Example: Speed 20 → deviation=-10

### Max Speed Deviation
- **Positive value**: Creature's maximum speed (across all movement types) exceeds 30ft
  - Example: Ground 30, Fly 60 → max_speed=60 → deviation=+30
- **Zero**: Max speed is standard 30ft
- **Negative value**: Creature is slow in all movement types

## Benefits

1. **More Interpretable**: Deviation values are easier to understand than raw values
   - "Being Large when Medium is expected adds X HP" is clearer than "Large size adds X HP"

2. **CR-Aware**: The model now accounts for CR-appropriate expectations
   - A CR 5 Large creature is expected, but a CR 25 Large creature is unusually small

3. **Consistent Pattern**: Matches existing baseline-deviation features (ac_deviation, attack_deviation, etc.)

4. **Better Learning**: Phase 3 model can learn how deviations from expectations affect HP

## Verification

Run the verification script to check implementation:
```bash
python3 test_changes/verify_baselines.py
```

All checks passed ✓

## Next Steps

1. **Run the notebook** to apply changes and retrain models:
   ```bash
   jupyter nbconvert --to notebook --execute notebooks/three_tier_hp_model.ipynb
   ```

2. **Verify model training** completes without errors

3. **Test predictions** using `investigate_creature()`:
   ```python
   investigate_creature('Roper')
   investigate_creature('Ancient Red Dragon')
   ```

4. **Check feature contributions** in the output to see how size/speed deviations impact HP

5. **Compare model performance** - check if MAE/error metrics improve with new features

## Expected Impact

The models will now learn:
- How much HP bonus/penalty unusually large/small creatures have
- How much HP adjustment fast/slow creatures need
- Whether movement capabilities beyond walking speed affect HP

This should improve predictions for creatures that deviate from CR-appropriate size/speed expectations.
