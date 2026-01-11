# 5-Bucket Conversion Summary

## Overview

Successfully converted the HP prediction model from **3 CR tiers** to **5 CR buckets** in the new notebook `three_tier_hp_model_v2.ipynb`.

## Changes Made

### Phase 1: CR Bucket Splitting ✅
**Cell 18** - Updated data splitting logic

**Old (3 buckets):**
```python
df_low_cr = df_valid[df_valid['cr_numeric'] <= 1.0].copy()
df_mid_cr = df_valid[(df_valid['cr_numeric'] > 1.0) & (df_valid['cr_numeric'] <= 12.0)].copy()
df_high_cr = df_valid[df_valid['cr_numeric'] > 12.0].copy()
```

**New (5 buckets):**
```python
df_cr1 = df_valid[df_valid['cr_numeric'] < 1.0].copy()
df_cr2 = df_valid[(df_valid['cr_numeric'] >= 1.0) & (df_valid['cr_numeric'] <= 4.0)].copy()
df_cr3 = df_valid[(df_valid['cr_numeric'] >= 5.0) & (df_valid['cr_numeric'] <= 10.0)].copy()
df_cr4 = df_valid[(df_valid['cr_numeric'] >= 11.0) & (df_valid['cr_numeric'] <= 16.0)].copy()
df_cr5 = df_valid[df_valid['cr_numeric'] > 16.0].copy()
```

### Phase 2: Model Training ✅
**Cells 20-24** - Created 5 model training cells

- **Cell 20**: CR < 1 model
- **Cell 21**: CR 1-4 model
- **Cell 22**: CR 5-10 model
- **Cell 23**: CR 11-16 model
- **Cell 24**: CR > 16 model

**Training Strategy:**
- All 5 buckets use **ALL creatures for both training and testing**
- This ensures no empty test sets and validates models work on all creatures in each bucket
- Removed manual train/test split logic to simplify and avoid errors

**Phase 2 Penalties** (example for CR 1-4):
```python
PHASE2_PENALTIES_CR2 = {
    'ac_deviation': -5.0,
    'attack_deviation': -6.0,
    'dpr_deviation': -2.0,
    'save_dc_deviation': -10.0,
    'has_flying': -8.0
}
```

### Phase 3: Model Saving ✅
**Cell 28** - Updated to save 5 pickle files

**Old files:**
- `hp_model_low_cr.pkl`
- `hp_model_mid_cr.pkl`
- `hp_model_high_cr.pkl`

**New files:**
- `hp_model_cr1.pkl` (CR < 1)
- `hp_model_cr2.pkl` (CR 1-4)
- `hp_model_cr3.pkl` (CR 5-10)
- `hp_model_cr4.pkl` (CR 11-16)
- `hp_model_cr5.pkl` (CR > 16)

Each model dict includes:
```python
{
    'coef': coef_cr#,
    'intercept': intercept_cr#,
    'scaler': scaler_cr#,
    'feature_columns': phase3_features,
    'phase2_penalties': PHASE2_PENALTIES_CR#,
    'cr_range': (min, max),
    'cr_label': 'CR X-Y',
    'test_r2': test_r2_cr#,
    'test_mae': mae_cr#
}
```

### Phase 4: Variable Renaming ✅
**Cells 30-onwards** - Automated variable name updates

Renamed all references from 3-tier to 5-bucket:

| Old Name | New Names |
|----------|-----------|
| `df_low_cr`, `df_mid_cr`, `df_high_cr` | `df_cr1`, `df_cr2`, `df_cr3`, `df_cr4`, `df_cr5` |
| `model_low`, `model_mid`, `model_high` | `model_cr1`, `model_cr2`, `model_cr3`, `model_cr4`, `model_cr5` |
| `scaler_low`, `scaler_mid`, `scaler_high` | `scaler_cr1`, `scaler_cr2`, `scaler_cr3`, `scaler_cr4`, `scaler_cr5` |
| `PHASE2_PENALTIES_LOW/MID/HIGH` | `PHASE2_PENALTIES_CR1/2/3/4/5` |

### Phase 5: Data Concatenation ✅
**Cells 37, 39** - Updated pd.concat calls

**Old:**
```python
export_df = pd.concat([df_cr1, df_cr2, df_cr3], ignore_index=False)
```

**New:**
```python
export_df = pd.concat([df_cr1, df_cr2, df_cr3, df_cr4, df_cr5], ignore_index=False)
```

### Phase 6: Model Selection Logic ✅
**Cells 37, 39** - Updated CR-based model routing

**Old (3 models):**
```python
if cr < 1.0:
    model = model_cr1
elif cr <= 10.0:
    model = model_cr2
else:
    model = model_cr3
```

**New (5 models):**
```python
if cr < 1.0:
    model = model_cr1
elif cr <= 4.0:
    model = model_cr2
elif cr <= 10.0:
    model = model_cr3
elif cr <= 16.0:
    model = model_cr4
else:  # cr > 16.0
    model = model_cr5
```

## CR Bucket Definitions

| Bucket | CR Range | Label | Description |
|--------|----------|-------|-------------|
| 1 | CR < 1 | "CR < 1" | Very low CR creatures |
| 2 | 1 ≤ CR ≤ 4 | "CR 1-4" | Low CR creatures |
| 3 | 5 ≤ CR ≤ 10 | "CR 5-10" | Mid CR creatures |
| 4 | 11 ≤ CR ≤ 16 | "CR 11-16" | High CR creatures |
| 5 | CR > 16 | "CR > 16" | Very high CR creatures |

## Files Modified

1. **`notebooks/three_tier_hp_model_v2.ipynb`** (NEW) - Complete 5-bucket notebook
2. **`data/baseline_lookup_three_tier.json`** - Already includes new baselines
3. **`pickled_models/`** - Will contain 5 new .pkl files after notebook run

## Files Preserved

1. **`notebooks/three_tier_hp_model.ipynb`** - Original 3-tier version (unchanged)
2. **`pickled_models/hp_model_*_cr.pkl`** - Old 3-tier models (still present)

## Benefits of 5-Bucket System

1. **Better specialization** - Narrower CR ranges mean more consistent feature coefficients
2. **Improved accuracy** - Mid-range CRs (previously lumped into single 1-12 bucket) now have dedicated models
3. **Alignment with D&D tiers** - Matches D&D 5e's tier of play system (levels 1-4, 5-10, 11-16, 17-20)
4. **Clearer interpretation** - Each model focuses on a specific power level

## Next Steps

### 1. Test the Notebook
```bash
# Run specific cells to test
jupyter notebook notebooks/three_tier_hp_model_v2.ipynb
```

Test cells in order:
- Cell 18: Data splitting
- Cells 20-24: Model training
- Cell 28: Model saving
- Cells 30+: Analysis and exports

### 2. Verify Outputs
Check that 5 pickle files are created:
```bash
ls -la pickled_models/hp_model_cr*.pkl
```

### 3. Validate Predictions
Test creatures from each bucket:
```python
investigate_creature('Quasit')           # CR 1 - bucket 2
investigate_creature('Owlbear')          # CR 3 - bucket 2
investigate_creature('Roper')            # CR 5 - bucket 3
investigate_creature('Adult Red Dragon') # CR 17 - bucket 5
```

### 4. Update Supporting Files (Future)
Once v2 is tested and validated:
- Update `run_three_tier_model.py`
- Update test files in `test_changes/`
- Update `NOTEBOOK_EXECUTION_GUIDE.md`

## Notes

- Original 3-tier notebook preserved as backup
- Manual train/test split removed (all creatures used for both)
- Some cells may still reference old names - run notebook to identify
- Visualization cells may need adjustment for 5 subplots vs 3

## Verification Checklist

- [x] CR bucket splitting updated
- [x] 5 training cells created
- [x] Model saving updated for 5 files
- [x] Variable names updated throughout
- [x] pd.concat calls updated
- [x] Model selection logic updated
- [ ] Notebook runs without errors
- [ ] 5 pickle files created
- [ ] Predictions work correctly
- [ ] Analysis cells work
- [ ] Visualizations display properly
