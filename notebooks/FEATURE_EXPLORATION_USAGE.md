# Feature Exploration Notebook - Usage Guide

## Overview

The feature_exploration.ipynb notebook identifies 13 creature archetypes to enhance HP model feature engineering. It now includes dynamic path detection for flexible execution.

## Dynamic Paths

The notebook automatically detects its execution context and sets paths accordingly:

### Running from Project Root
```bash
cd /workspaces/matrix_v0
jupyter notebook notebooks/feature_exploration.ipynb
```
**Paths used:**
- `DATA_DIR = 'data'`
- `PICKLED_MODELS_DIR = 'pickled_models'`
- `OUTPUT_DIR = 'data'`

### Running from Notebooks Directory
```bash
cd /workspaces/matrix_v0/notebooks
jupyter notebook feature_exploration.ipynb
```
**Paths used:**
- `DATA_DIR = '../data'`
- `PICKLED_MODELS_DIR = '../pickled_models'`
- `OUTPUT_DIR = '../data'`

## Input Files

The notebook reads from:
- `{DATA_DIR}/dnd5e_monsters_from_json.csv` - Raw monster data (382 creatures)
- `{DATA_DIR}/engineered_features.csv` - HP model features
- `{DATA_DIR}/feature_contributions.csv` (optional) - For HP correlation analysis

## Output Files

The notebook creates:
- `{OUTPUT_DIR}/creature_archetypes.csv` - All 382 creatures with 13 archetype scores

## Archetype Categories

### Hierarchy Types (5)
1. **Boss** - Legendary actions, highest in family, leader titles
2. **Lieutenant** - Mid-chain, tactical roles, ally interactions
3. **Minion** - Lowest in family, pack tactics
4. **Solo Challenge** - Multi-target abilities without legendary actions
5. **Enhanced** - Greater/Dire/Elder variants

### Combat Roles (8)
6. **Brute** - High HP + damage, low AC + speed
7. **Tank** - High AC + HP, lower damage
8. **Skirmisher** - High mobility, higher AC, lower HP
9. **Spellcaster** - Full casters (5+ spell levels = 0.9) vs limited (0.6)
10. **Controller** - Condition imposers, battlefield manipulation
11. **Artillery** - High ranged DPR, lower melee/HP
12. **Ambusher** - Stealth, surprise mechanics
13. **Swarm** - Explicit swarm creatures

## Key Features

### JSON Parsing (Borrowed from three_tier_hp_model_v2)
- ✅ **Multiattack counting** - Parses Actions JSON to extract attack counts
- ✅ **Legendary actions detection** - Properly handles JSON format
- ✅ **Damage calculation** - Converts dice notation to average damage

### Validated Findings
- **132 creatures** have multiattack (2-7 attacks)
- **32 creatures** have legendary actions (all are bosses)
- **Multiattack vs CR correlation: 0.397** (positive, as expected!)

### Family Detection
- **18 creature families** identified (e.g., dragon lineages)
- Assigns positions: boss (highest CR), lieutenant (middle), minion (lowest)

### CR-Relative Percentiles
- Compares creatures to others within ±2 CR
- Enables cross-CR archetype detection

## Quick Start

```bash
# From project root
cd /workspaces/matrix_v0
jupyter notebook notebooks/feature_exploration.ipynb
```

**Or run all cells programmatically:**
```bash
jupyter nbconvert --to notebook --execute notebooks/feature_exploration.ipynb --ExecutePreprocessor.timeout=600
```

## Expected Runtime

- **Data loading**: < 1 second
- **Family detection**: < 1 second
- **Archetype scoring**: 2-5 seconds
- **CR percentiles**: 5-10 seconds (calculates for each creature)
- **Visualizations**: 2-3 seconds
- **Total**: ~15-20 seconds

## Output Format

### creature_archetypes.csv Columns:
```
Name, cr_numeric, HP, AC,
boss_score, lieutenant_score, minion_score, solo_challenge_score, enhanced_version_score,
brute_score, tank_score, skirmisher_score, spellcaster_score, controller_score,
ambusher_score, swarm_score, artillery_score,
archetypes, family_position, family_size
```

### Example Output:
```csv
Name,cr_numeric,boss_score,brute_score,tank_score,archetypes
Adult Red Dragon,17.0,1.0,0.7,0.4,"Boss, Brute"
Goblin,0.25,0.0,0.0,0.0,"Minion"
Archmage,12.0,1.0,0.0,0.0,"Boss, Spellcaster"
```

## Troubleshooting

### Path Issues
If you see "File not found" errors:
1. Check current directory: `os.getcwd()`
2. Verify paths printed in Cell 1
3. Ensure you're running from project root or notebooks directory

### Missing Data
If `engineered_features.csv` is missing:
```bash
# Run the HP model first to generate engineered features
jupyter nbconvert --to notebook --execute notebooks/three_tier_hp_model_v2.ipynb
```

### HP Correlation Analysis Fails
This is optional - the notebook will skip it gracefully if prediction files don't exist.

## Next Steps

After running the notebook:

1. **Analyze archetype distributions** - Which are most common?
2. **Check HP correlation** - Which archetypes are mispredicted?
3. **Integrate findings** - Add high-value archetypes as features in three_tier_hp_model_v2
4. **Validate patterns** - Do bosses really have higher HP than predicted?

## Files Modified

- `notebooks/feature_exploration.ipynb` - Main notebook with all 13 archetypes
- Cell 1: Dynamic path detection
- Cell 3: Data loading with dynamic paths
- Cell 7: JSON-based multiattack parsing
- Cell 10: JSON-based legendary actions detection
- Cell 33: Output with dynamic path
- Cell 35: HP correlation with dynamic paths
