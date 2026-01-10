# Fixes Applied to three_tier_hp_model.ipynb

## 1. DPR Parser Fix ✅

**Cell**: 12  
**Function**: `parse_dpr_from_json()`

**Problem**: 
- Roper calculated as 88 DPR instead of 22 DPR
- Parser was applying generic "makes four attacks" to bite damage
- Ignored that "four attacks" referred to non-damaging tendrils

**Solution**:
- Added 4 new regex patterns to match specific attack names
- Improved fallback logic to check if generic count refers to non-damaging attacks
- Only applies fallback when exactly one damaging attack exists

**Impact**:
- Roper: 88 → 22 DPR (-66)
- Other creatures with grapple/utility attacks will also be corrected

## 2. Legendary Actions Parser Restoration ✅

**Cell**: 12  
**Function**: `parse_legendary_actions_dpr()`

**Problem**:
- Function was accidentally removed during DPR parser update
- Caused NameError when running notebook

**Solution**:
- Restored the complete `parse_legendary_actions_dpr()` function
- Uses knapsack optimization to find damage-maximizing legendary action combinations
- Extracts both DPR and conditions from legendary actions

## Verification

All required functions now present in cell 12:
- ✓ parse_attack_bonus
- ✓ parse_save_dc
- ✓ calculate_average_damage
- ✓ parse_dpr_from_json (FIXED)
- ✓ parse_legendary_actions_dpr (RESTORED)
- ✓ parse_spellcasting

## Next Steps

The notebook is ready to run. Execute with:

```bash
cd /workspaces/matrix_v0
python3 run_three_tier_model.py
```

Expected changes:
1. DPR values will be corrected for creatures like Roper
2. This will cascade to dpr_deviation, phase2_dpr_contribution, and final HP predictions
3. Feature contribution analysis will show updated values
4. Model predictions should improve for affected creatures
