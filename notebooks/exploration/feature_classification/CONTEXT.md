# Feature Classification Project

## Purpose

Comprehensive cataloging and classification of D&D 5e monster traits, actions, and abilities to:

1. **Ensure completeness** - Verify all meaningful effects are captured in `1_feature_engineering.ipynb`
2. **Identify gaps** - Find patterns that appear frequently but have no corresponding engineered feature
3. **Estimate HP costs** - Link discovered patterns to HP impact via `feature_contributions.csv`
4. **Create a trait menu** - Enable custom monster creation with known HP costs

## Data Sources

- **Primary**: `data/dnd5e_monsters_from_json.csv` - Full monster dataset with JSON-formatted traits/actions
- **Reference**: `data/feature_contributions.csv` - HP costs per feature from trained models
- **Reference**: `data/engineered_features.csv` - Full engineered feature set

## Prior Work

### Existing Analysis
- `notebooks/exploration/cr1_4_prediction_analysis_findings.md` - Identified patterns correlated with prediction errors
- `notebooks/exploration/multiattack_parser_issues.md` - DPR parsing patterns and fixes

### Existing Parsers
- `notebooks/helper_files/parsers.py` - Current parsing functions (source for CORE_PATTERN_DEFINITIONS)
- `notebooks/helper_files/feature_config.py` - Feature definitions (PHASE2_FEATURES, get_phase3_features)

### Core Pattern Sources (from parsers.py)
The following parser functions were mined for patterns and integrated into Phase 1 as CORE_PATTERN_DEFINITIONS (30 patterns):
- `has_advantage_condition()` - Pack Tactics, Blood Frenzy, Reckless, Ambusher, Assassinate, etc.
- `has_disadvantage_condition()` - Sunlight Sensitivity, Sunlight Weakness, Light Sensitivity
- `has_attackers_advantage()` - Attack rolls against target have advantage
- `parse_charge_bonus_attack()` - Charge, Pounce, Rampage, Trampling
- `extract_spellcaster_level()` - Spellcaster level extraction
- `parse_legendary_actions()` - Legendary action count
- `parse_dpr_from_json()` - Multiattack counts, conditional damage patterns

### Key Findings from Prior Analysis

**Patterns correlated with OVER-prediction (monster has LESS HP than expected):**
- Shapechange/polymorph (14.5% of bad predictions)
- Regains HP abilities
- Failed save effects

**Patterns correlated with UNDER-prediction (monster has MORE HP than expected):**
- Grapple/restrain control (13% of under-predictions)
- Tank/controller archetypes
- Prone infliction

## Terminology

- **Trait**: Passive ability (e.g., Pack Tactics, Magic Resistance, Sunlight Sensitivity)
- **Action**: Active ability requiring action economy (e.g., Multiattack, Breath Weapon, Spellcasting)
- **Pattern**: Regex or keyword that identifies a mechanical effect in text
- **Feature**: Engineered numeric value derived from patterns (e.g., `has_magic_resistance`, `inflicts_prone`)
- **HP Cost**: The estimated HP adjustment a feature contributes to predicted HP

## Relationship to HP Prediction Model

```
Raw Monster Data → Pattern Detection → Feature Engineering → HP Prediction
                   (This project)      (1_feature_engineering)  (2_model_training)
```

This project sits between raw data and feature engineering, ensuring we're capturing all relevant effects.

**IMPORTANT**: The core workflow notebooks (`1_feature_engineering.ipynb`, `2_model_training.ipynb`, `feature_config.py`) are protected and must not be modified without explicit user approval. This project is for **discovery and analysis only**. Any new features identified here require user review and approval before implementation in the core model.

## Output Files

All outputs go to `notebooks/exploration/feature_classification/data/`:

### Phase 1 Outputs (Pattern Extraction)
- `trait_catalog.parquet` - All trait instances with pattern detection columns (notebook, core, combined)
- `action_catalog.parquet` - All action instances with pattern detection columns
- `trait_summary.csv` - Unique traits by normalized name with frequency and pattern coverage
- `action_summary.csv` - Unique actions by normalized name with frequency and pattern coverage
- `pattern_frequencies.csv` - Pattern occurrence counts across all traits and actions
- `multiattack_analysis.csv` - Multiattack descriptions with complexity categorization
- `multiattack_pattern_frequencies.csv` - Multiattack-specific pattern counts

### Future Phase Outputs
- `feature_mapping.csv` - Map of patterns to engineered features (Phase 2)
- `unmapped_patterns.csv` - Patterns with no corresponding feature / gaps (Phase 2)
- `feature_hp_costs.csv` - HP costs aggregated by feature (Phase 3)
- `trait_menu.csv` - Final menu for custom monster building (Phase 4)
