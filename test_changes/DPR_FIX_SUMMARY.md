# DPR Parser Fix Summary

## Problem Identified

The DPR parser was incorrectly calculating damage for creatures with complex multiattacks that include non-damaging attacks.

### Example: Roper

**Multiattack Description:**
> "The roper makes four attacks with its tendrils, uses Reel, and makes one attack with its bite."

**Actions:**
- **Tendril**: Grapples target (no damage)
- **Bite**: 4d8 + 4 damage (average: 22)
- **Reel**: Pulls grappled creatures (no damage)

**Before Fix:**
- Parser found "makes four attacks" → 4 × 22 = **88 DPR** ❌
- Ignored that "four attacks" referred to tendrils (non-damaging)

**After Fix:**
- Parser matches "one attack with its bite" → 1 × 22 = **22 DPR** ✓

## What Was Fixed

### Improved Attack Matching

Added better regex patterns to specifically match attack names in multiattack descriptions:

1. `"(\w+)\s+{attack_name}\s+attacks?"` - "four bite attacks"
2. `"(\w+)\s+attacks?\s+with\s+(?:its\s+)?{attack_name}"` - "four attacks with its bite"
3. `"makes?\s+(\w+)\s+{attack_name}\s+attacks?"` - "makes one bite attack"
4. `"makes?\s+(\w+)\s+attacks?\s+with\s+(?:its\s+)?{attack_name}"` - "makes one attack with its bite"

### Improved Fallback Logic

The generic fallback ("makes X attacks") now:
- Only applies when there's exactly ONE damaging attack type
- Checks if the generic count refers to a different (non-damaging) attack
- Defaults to 1 attack if a specific count is found for the damaging attack

## Expected Impact

### Creatures with DPR Changes

The fix will primarily affect creatures with:
- Multiple attack types where some don't deal damage (grapple, utility)
- Complex multiattack descriptions that mention non-damaging actions

**Examples:**
- **Roper**: 88 → 22 DPR (-66)
- Similar creatures with grapple/utility attacks

### Downstream Effects

DPR is used in Phase 2 calculations, so this fix will:
1. Change `dpr_deviation` for affected creatures
2. Change `phase2_dpr_contribution` to HP
3. Change `hp_after_phase2` baseline
4. Change final HP predictions for these creatures

## Verification

To verify the fix works correctly before re-running the full notebook:

```bash
cd /workspaces/matrix_v0/test_changes
python3 verify_dpr_fix.py
```

This will show DPR changes for Roper and other affected creatures.

## Files Modified

- `notebooks/three_tier_hp_model.ipynb` - Cell 12: Updated `parse_dpr_from_json()` function

## Testing

Test script created: `test_changes/test_dpr_parser.py`
- Tests Roper case (passes ✓)
- Tests simple multiattack (passes ✓)
- Tests no multiattack (passes ✓)
