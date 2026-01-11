# Passive Perception Rolled into Save DC Deviation

## Change Summary

Passive perception is no longer a separate Phase 3 feature. Instead, it's incorporated into `save_dc_deviation` in Phase 2.

## Rationale

Passive perception should only matter for HP if it's **exceptionally high** for the creature's CR - indicating heightened awareness that makes the creature harder to surprise or ambush (effectively harder to kill).

## Implementation

### Phase 2 (Cell 15)

Added calculation after `save_dc_deviation`:

```python
# Add passive perception bonus to save_dc_deviation if it exceeds baseline + 1
# Only counts exceptional passive perception (e.g., creature with Alert feat)
df['passive_perception_bonus'] = (df['passive_perception'] - (df['dc_baseline'] + 1)).clip(lower=0)
df['save_dc_deviation'] = df['save_dc_deviation'] + df['passive_perception_bonus']
```

**Logic:**
- Baseline save DC for the CR is used as the threshold
- Only passive perception that exceeds `(dc_baseline + 1)` counts
- The bonus is added to `save_dc_deviation`
- This gets multiplied by the Phase 2 penalty coefficient (e.g., -10 HP per point)

**Example:**
- CR 5 creature: dc_baseline = 13
- Passive perception = 16
- Bonus = max(0, 16 - 14) = 2
- Added to save_dc_deviation
- Impact: 2 × (-10) = -20 HP in Phase 2

### Phase 3 (Cell 16)

Removed `passive_perception` from phase3_features:

```python
phase3_features = [
    # ... other features ...
    # 'passive_perception',  # Rolled into save_dc_deviation
    # ... more features ...
]
```

## Impact

- **Phase 3 features**: Reduced from 41 to 40 features (passive_perception removed)
- **Condition infliction features**: Still dynamically added (11 features)
- **Total Phase 3 features**: Now 40 + 11 = 51 features (was 41 + 11 = 52)

Wait, that doesn't match. Let me recount...

Actually:
- **Base Phase 3 features**: 29 defined features (after removing passive_perception)
- **Condition infliction features**: 11 added dynamically
- **Total**: 29 + 11 = 40 features

## Benefits

1. **Clearer semantics**: Passive perception treated as a combat awareness stat (like save DC)
2. **Only exceptional values matter**: Normal passive perception doesn't affect HP
3. **Phase 2 consistency**: All "combat baseline deviation" features in one place
4. **Simpler Phase 3**: One less feature to learn coefficients for

## Verification

After re-running the notebook:

```python
# Check that passive_perception is not in phase3_features
assert 'passive_perception' not in phase3_features

# Check that passive_perception_bonus is calculated
assert 'passive_perception_bonus' in df.columns

# Check that it's added to save_dc_deviation
# Creatures with high passive perception should have higher save_dc_deviation
```
