# Notebook Execution Guide

This guide explains how to run the newly created and updated notebooks for the correlation analysis and four-phase HP model.

## Overview

Two notebooks have been created/updated:
1. **correlation_analysis.ipynb** - NEW: Analyzes feature correlations and multicollinearity
2. **three_tier_hp_model.ipynb** - UPDATED: Now implements the four-phase model with Phase 1.5

## Execution Order

Run the notebooks in this order:

### 1. Correlation Analysis (Run First)

This notebook will help you understand:
- Which features are highly correlated (multicollinearity)
- Whether flying should move to Phase 2
- Why some Phase 3 features show positive HP contributions
- What the flying penalty coefficient should be

**Command:**
```bash
cd /workspaces/matrix_v0
python3 run_correlation_analysis.py
```

**Expected Output:**
- Correlation matrices for Phase 2 and Phase 3 features
- VIF scores showing multicollinearity (flags features with VIF > 10)
- Cross-correlations between Phase 2 and Phase 3
- Flying investigation (CR patterns, creature type analysis)
- Recommendations on features to remove and flying penalty coefficient

**Review the results before running the next notebook!**

### 2. Three-Tier HP Model (Run Second)

This notebook will train the updated four-phase model:
- Phase 1: CR baseline HP
- Phase 1.5: Resistances/immunities (fixed penalties with 75% cap)
- Phase 2: Combat stat deviations + flying (fixed penalties)
- Phase 3: Remaining features (learned residual)

**Command:**
```bash
cd /workspaces/matrix_v0
python3 run_three_tier_model.py
```

**What it does:**
1. Parses legendary actions for damage and conditions
2. Integrates legendary DPR into total_dpr
3. Applies Phase 1.5 resistance/immunity penalties
4. Trains three CR-specific models (low ≤ 1, mid 1-12, high > 12)
5. Exports models to:
   - `pickled_models/hp_model_low_cr.pkl`
   - `pickled_models/hp_model_mid_cr.pkl`
   - `pickled_models/hp_model_high_cr.pkl`
   - `monster-builder-v2/model_data.json`

## Changes Made to three_tier_hp_model.ipynb

### 1. Legendary Actions Parsing
- Added comprehensive parser that extracts damage dice and conditions
- Uses knapsack-style optimization to maximize damage within action budget
- Example: Ancient Bronze Dragon with 3 actions
  - Wing Attack (2 cost): 2d6+9 damage + prone condition
  - Tail Attack (1 cost): 2d8+9 damage
  - Optimal: Wing (2) + Tail (1) = 34 DPR + prone

### 2. Integrated Legendary DPR
- `total_dpr = estimated_dpr + legendary_dpr`
- DPR deviation now uses total_dpr instead of just estimated_dpr
- Removed `has_legendary_actions` feature (effects captured in DPR/conditions)

### 3. Added Phase 1.5: Resistances/Immunities
- Each immunity: -50% of Phase 1 HP
- Each resistance: -25% of Phase 1 HP
- Combined cap: 75% of Phase 1 HP
- Example: 100 HP baseline, 2 immunities (100 HP) + 3 resistances (75 HP)
  - Total penalty: 175 HP → capped at 75 HP
  - HP after Phase 1.5: 25 HP

### 4. Updated Phase 2
- Now starts from `hp_after_phase1_5` instead of `hp_baseline`
- All three CR models (low, mid, high) updated

### 5. Updated Phase 3 Features
- **Removed** (now handled elsewhere):
  - `has_legendary_actions_scaled` → handled via total_dpr
  - `resistance_count` → Phase 1.5
  - `immunity_count` → Phase 1.5
- **Kept**: 42 remaining features (down from 45)
  - Movement, senses, abilities, conditions, etc.
  - Still includes `vulnerability_count` and `condition_immunity_count`

## Expected Outcomes

After running both notebooks, you should see:

### From Correlation Analysis:
- List of features with VIF > 10 (severe multicollinearity)
- High correlation pairs (|r| > 0.7)
- Flying-CR correlation and recommended penalty coefficient
- Features with positive HP correlation (and why)

### From Three-Tier Model:
- Improved model performance (higher R², lower MAE)
- Fewer paradoxical positive coefficients in Phase 3
- Better interpretability (clearer phases)
- Models ready for web app integration

## Next Steps After Execution

1. **Review correlation analysis results**
   - Open `notebooks/correlation_analysis.ipynb` to see outputs
   - Check which features should be removed due to multicollinearity
   - Note the flying penalty recommendation

2. **Review model performance**
   - Open `notebooks/three_tier_hp_model.ipynb` to see outputs
   - Compare R² and MAE to previous versions
   - Check Phase 3 coefficients (should have fewer positive values)

3. **Optional: Refine based on correlation analysis**
   - If correlation analysis suggests removing features, update phase3_features list
   - Re-run three_tier_hp_model.ipynb

4. **Test in web app**
   - The updated `monster-builder-v2/model_data.json` is ready to use
   - Test creature HP predictions with the new four-phase model

## Troubleshooting

### If correlation_analysis.ipynb fails:
- Check that `data/engineered_features.csv` exists
- Ensure all required packages are installed: pandas, numpy, matplotlib, seaborn, scipy, statsmodels

### If three_tier_hp_model.ipynb fails:
- Check that `data/dnd5e_monsters_from_json.csv` exists
- Check that `data/lazy_5e_monster_stats_by_cr.csv` exists
- Ensure all required packages are installed

### If you see import errors:
```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels scikit-learn nbformat nbconvert
```

## Summary

The notebooks are now ready to run. Execute them in order:
1. `python3 run_correlation_analysis.py` (creates insights)
2. Review correlation results
3. `python3 run_three_tier_model.py` (trains models)
4. Review model performance
5. Test in web app

Both notebooks will save their outputs back to the .ipynb files, so you can review them in Jupyter or VS Code.
