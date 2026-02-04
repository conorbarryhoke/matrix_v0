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
**Status**: COMPLETE
**Notebook**: `notebooks/1_pattern_extraction.ipynb`

### Objectives
- Extract all unique trait names and action names with frequencies
- Identify text patterns using regex (saving throws, damage types, conditions, etc.)
- Catalog wording variations for similar effects
- Integrate patterns from core parsers (`parsers.py`) alongside notebook-defined patterns
- Analyze multiattack string complexity and categorize parsing difficulty
- Consolidate action names into weapon/natural weapon categories

### Notebook Structure (8 sections, 51 cells)
1. **Section 1: Extract All Traits** — 574 trait instances, 167 unique names
2. **Section 2: Extract All Actions** — 1006 action instances, 104 unique normalized names (consolidated from 207)
3. **Section 3: Pattern Detection** — 61 notebook patterns (PATTERN_DEFINITIONS) + 30 core patterns (CORE_PATTERN_DEFINITIONS from parsers.py)
4. **Section 4: Identify Unmatched Traits/Actions** — Uses combined `pattern_count_any` to find gaps
5. **Section 5: High-Priority Pattern Analysis** — HP max reduction, shapechange, death burst, undead fortitude, ethereal movement
6. **Section 6: Save Outputs** — Exports parquet and CSV files
7. **Section 7: Quick Reference** — Trait and action summaries with notebook, core, and combined pattern columns
8. **Section 8: Multiattack Pattern Analysis** — 21 multiattack-specific patterns, complexity categorization

### Pattern Sources
- **PATTERN_DEFINITIONS** (61 patterns): Saving throws, conditions, damage, HP manipulation, defensive abilities, regeneration, movement, shapechanging, attack modifiers, stealth/hide, recharge, death effects, spellcasting, aura, multiattack, swallow, charm, fear, gaze, life drain
- **CORE_PATTERN_DEFINITIONS** (30 patterns from parsers.py): Advantage/disadvantage conditions, charge/pounce/rampage, spellcaster level, legendary actions, multiattack counts, conditional damage, prone infliction
- **MULTIATTACK_PATTERNS** (21 patterns): Attack counts, OR alternatives, specific attack references, constraints, conditionals, form-dependent, weapon-specific

### Action Name Consolidation
Action `name_normalized` consolidates attack types using `data/dnd5e_weapons.csv` and a curated natural weapons set:
- **Melee Weapon** (150 instances) — Manufactured melee weapons matched via CSV lookup + aliases + substring matching
- **Ranged Weapon** (51 instances) — Manufactured ranged weapons; thrown melee weapons with explicit `(Ranged)` suffix
- **Natural Weapon** (413 instances) — Strict body-part attacks: bite, claw, tail, slam, gore, hooves, beak, talons, sting, etc. (35 entries)
- **Unconsolidated** (~392 instances) — Multiattack, breath weapons, special abilities, etc. retain their original normalized names

Trait `name_normalized` is unaffected — traits use the original `normalize_trait_name()` (parenthetical stripping only).

Candidates for manual review (not auto-classified): rock, fist, unarmed strike, rotting fist, fling, blood drain, slash, rotting touch, withering touch, poison jab, shock.

### Column Schema
Each catalog (trait/action) includes three pattern tracking layers:
- `patterns`, `pattern_count`, `patterns_str` — Notebook patterns only
- `patterns_core`, `pattern_count_core`, `patterns_str_core` — Core parsers.py patterns only
- `patterns_any`, `pattern_count_any`, `patterns_str_any` — Combined (union of both sources)

### Outputs
- `data/trait_catalog.parquet` - All traits with pattern detection columns
- `data/action_catalog.parquet` - All actions with pattern detection columns
- `data/trait_summary.csv` - Unique traits by name with frequency and pattern coverage
- `data/action_summary.csv` - Unique actions by name with frequency and pattern coverage
- `data/pattern_frequencies.csv` - Pattern occurrence counts (53 patterns detected at least once)
- `data/multiattack_analysis.csv` - 160 multiattack descriptions with complexity categories
- `data/multiattack_pattern_frequencies.csv` - Multiattack-specific pattern counts

### Key Results
- Traits with notebook patterns: 230/574 (40.1%)
- Actions with notebook patterns: 377/1006 (37.5%)
- Multiattack creatures: 160, of which 31 (19.4%) have potentially problematic parsing patterns
- Multiattack complexity: 55.6% simple_specific, 15.0% or_alternative, 6.9% simple_count, 3.1% conditional

### Key Patterns to Detect
1. **Damage patterns**: "Xd6 damage", "plus X damage", "taking X damage"
2. **Save patterns**: "DC X [ability] saving throw", "must succeed on a"
3. **Condition patterns**: "is [condition]", "becomes [condition]", "[condition] until"
4. **Control patterns**: "grappled", "restrained", "escape DC"
5. **Defensive patterns**: "resistance to", "immune to", "regenerates"
6. **Movement patterns**: "can't move", "speed is reduced", "teleport"
7. **Special mechanics**: "reduce hit point maximum", "can't regain hit points"
8. **Stealth/Hide patterns**: "Hide action as a bonus action", "advantage on Stealth checks"
9. **Core parser patterns**: Pack Tactics, Blood Frenzy, Sunlight Sensitivity, Charge, Pounce, etc.

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
| 2026-01-29 | Setup | Created folder structure and documentation | CONTEXT.md, PLAN.md |
| 2026-01-29 | Phase 1 | Created pattern extraction notebook | Sections 1-7, 61 patterns |
| 2026-01-30 | Phase 1 | Added Section 8: Multiattack Pattern Analysis | 21 multiattack patterns, complexity categorization |
| 2026-01-30 | Phase 1 | Added Hide/Stealth patterns | bonus_action_hide, stealth_advantage |
| 2026-01-30 | Phase 1 | Integrated core patterns from parsers.py | 30 patterns, 3-layer column schema (notebook/core/combined) |
| 2026-01-30 | Phase 1 | Updated Section 4 to use combined patterns | pattern_count_any for gap analysis |
| 2026-02-04 | Data | Created `data/dnd5e_weapons.csv` | 37 SRD weapons with weapon_category, average_damage |
| 2026-02-04 | Phase 1 | Added action name consolidation | Melee/Ranged/Natural Weapon categories, 207→104 unique names |

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
