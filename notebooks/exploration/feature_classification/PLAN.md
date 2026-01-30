# Feature Classification Plan

## Overview

4-phase approach to catalog all monster traits/actions, map to engineered features, and estimate HP costs.

---

## IMPORTANT: Core Workflow Protection

The following notebooks are part of the **core HP prediction workflow** and must NOT be modified without explicit user approval:

- `notebooks/1_feature_engineering.ipynb`
- `notebooks/2_model_training.ipynb`
- `notebooks/helper_files/feature_config.py`

**This feature classification project is for DISCOVERY and ANALYSIS only.**

When gaps are identified (patterns without corresponding features), the workflow is:

1. **Identify** - This project flags potential new features
2. **Review** - User reviews candidates and decides which to pursue
3. **Approve** - User explicitly requests addition (one at a time, in bulk, or rejects)
4. **Implement** - Only then are core notebooks modified

Features may be rejected for any reason (low impact, edge cases, complexity, etc.).

---

## Phase 1: Pattern Extraction
**Status**: IN PROGRESS
**Notebook**: `notebooks/1_pattern_extraction.ipynb`

### Objectives
- Extract all unique trait names and action names with frequencies
- Identify text patterns using regex (saving throws, damage types, conditions, etc.)
- Catalog wording variations for similar effects

### Outputs
- `data/trait_catalog.parquet` - All traits with metadata
- `data/action_catalog.parquet` - All actions with metadata
- `data/pattern_frequencies.csv` - Pattern occurrence counts

### Key Patterns to Detect
1. **Damage patterns**: "Xd6 damage", "plus X damage", "taking X damage"
2. **Save patterns**: "DC X [ability] saving throw", "must succeed on a"
3. **Condition patterns**: "is [condition]", "becomes [condition]", "[condition] until"
4. **Control patterns**: "grappled", "restrained", "escape DC"
5. **Defensive patterns**: "resistance to", "immune to", "regenerates"
6. **Movement patterns**: "can't move", "speed is reduced", "teleport"
7. **Special mechanics**: "reduce hit point maximum", "can't regain hit points"

---

## Phase 2: Feature Mapping
**Status**: NOT STARTED
**Notebook**: `notebooks/2_feature_mapping.ipynb`

### Objectives
- Map discovered patterns to existing features in `1_feature_engineering.ipynb`
- Identify GAPS (patterns not captured by current feature engineering)
- Create mapping dataframe linking patterns → features

### Outputs
- `data/feature_mapping.csv` - Pattern-to-feature mappings
- `data/unmapped_patterns.csv` - Patterns with no corresponding feature (GAPS)

### Mapping Categories
- **Direct match**: Pattern maps 1:1 to a feature (e.g., "Pack Tactics" → `has_advantage_condition`)
- **Indirect match**: Pattern contributes to a composite feature (e.g., "stunned" → `inflicts_stunned`)
- **Unmapped**: No current feature captures this pattern (GAPS to address)

---

## Phase 3: HP Cost Analysis
**Status**: NOT STARTED
**Notebook**: `notebooks/3_hp_cost_analysis.ipynb`

### Objectives
- Link mapped features to `feature_contributions.csv`
- Calculate aggregate HP costs per pattern/feature
- Identify high-impact patterns

### Outputs
- `data/feature_hp_costs.csv` - HP costs by feature with confidence intervals
- `data/pattern_hp_costs.csv` - HP costs aggregated by pattern

### Analysis Approach
1. Load `feature_contributions.csv`
2. For each pattern, find monsters with that pattern
3. Extract relevant feature contributions
4. Aggregate (mean, median, std) by pattern
5. Flag patterns where HP cost is uncertain (high variance)

---

## Phase 4: Categorization & Menu
**Status**: NOT STARTED
**Notebook**: `notebooks/4_trait_menu.ipynb`

### Objectives
- Define feature categories (offensive, defensive, utility, weakness)
- Classify all patterns into categories
- Create final "trait menu" for custom monster building

### Outputs
- `data/trait_menu.csv` - Complete menu with categories and HP costs
- `data/category_definitions.json` - Category taxonomy

### Proposed Categories
1. **Offensive**: Increases damage output (extra attacks, bonus damage, advantage)
2. **Defensive**: Increases survivability (resistances, regeneration, evasion)
3. **Control**: Limits enemy actions (conditions, grapple, movement reduction)
4. **Utility**: Non-combat benefits (senses, movement types, skill bonuses)
5. **Weakness**: Reduces effectiveness (sunlight sensitivity, vulnerabilities)
6. **Action Economy**: Affects turn economy (legendary actions, reactions, recharge)
7. **Resource Drain**: Long-term effects (HP max reduction, ability damage)

---

## Update Instructions

### Adding New Patterns (within this project)
1. Run Phase 1 notebook to regenerate catalogs
2. Re-run Phase 2 to update mappings (new patterns will appear in `unmapped_patterns.csv`)

### Refreshing HP Costs (after core model changes)
1. After `1_feature_engineering.ipynb` and `2_model_training.ipynb` are re-run
2. Re-run Phase 3 to recalculate HP costs with updated model

### Requesting New Features for Core Model
**This requires explicit user approval - do not modify core notebooks without permission.**

Workflow:
1. Identify candidate feature from `unmapped_patterns.csv` or analysis
2. Present to user with: pattern name, prevalence, expected HP impact, implementation complexity
3. User decides: approve (single), approve (batch), or reject
4. If approved, user will request implementation in core notebooks

---

## Progress Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-29 | Setup | Created folder structure and documentation | |
| 2026-01-29 | Phase 1 | Started pattern extraction notebook | |

---

## Known High-Priority Gaps (from prior analysis)

These patterns appear frequently but have no/weak feature coverage:

| Pattern | Prevalence | Current Status | Suggested Feature |
|---------|------------|----------------|-------------------|
| Shapechange/polymorph | 15% of bad predictions | Not captured | `has_shapechange` |
| Grapple + escape DC | 13% of under-predictions | Partial (`inflicts_grappled`) | `has_grapple_control` |
| Damage reduction | 9% of bad predictions | Not captured | `has_damage_reduction` |
| HP max reduction | Rare but impactful | Not captured | `reduces_hp_max` |
| Ethereal movement | Rare but extreme errors | Not captured | `has_ethereal` |
| Breath weapon | Common in dragons/mephits | Partial (via DPR) | Consider recharge value |
| Death burst | Mephits, some undead | Not captured | `has_death_burst` |
| Undead fortitude | Zombies | Not captured | `has_undead_fortitude` |
