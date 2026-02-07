# Feature Engineering Pipeline Context

This document describes how `1_feature_engineering.ipynb` works and where its
configuration lives. The goal is to reduce the amount of context that must be
inferred when making edits.

---

## Pipeline Overview

```
1_feature_engineering.ipynb          (this notebook)
    input:  data/dnd5e_monsters_from_json.csv          324 monsters (2014 SRD only)
            data/lazy_5e_monster_stats_by_cr.csv        34 CR baseline rows
            data/spellcaster_spell_features.csv         36 spellcasters w/ spell-based overrides
    output: notebooks/notebooks_io/engineered_features.parquet
                                                        ↓
2_model_training.ipynb
    reads:  engineered_features.parquet
    uses:   PHASE2_FEATURES, get_phase3_features(), MODEL_CONFIG  (from feature_config.py)
    output: pickled_models/hp_model_cr{1..5}.pkl
            data/engineered_features.csv                (adds predicted_hp, hp_delta, etc.)
            data/feature_contributions.csv
                                                        ↓
3_model_analysis.ipynb
    reads:  data/engineered_features.csv
            data/feature_contributions.csv
    output: analysis visualisations, notebooks/model_change_log.csv
                                                        ↓
execute_end_to_end.py                (orchestrator — runs all 3 in sequence)
```

---

## Notebook Sections (1_feature_engineering.ipynb)

| Section | Cells | What it does |
|---------|-------|--------------|
| Imports & Config | 0–9 | Path setup, imports from `helper_files/` |
| Load Raw Data | 10–12 | Load 3 CSVs, define `CONDITION_DEFINITIONS` (informational only) |
| Parse Basic Features | 13–31 | CR, AC, HP, speeds, size, proficiencies, senses, ability counts |
| Parse Combat Stats | 32–38 | Attack bonus, save DC (+ overrides), DPR (4-layer) |
| Parse Special Traits | 39–46 | Magic resistance / regeneration flags, condition infliction, advantage/disadvantage |
| Spellcasting | 47–56 | Detect spellcasters, merge enhanced stats from `spellcaster_spell_features.csv` |
| DMG Feature Costing | 57–58 | Detect 12 DMG features → `feature_ac`, `feature_attack`, `total_ac`, `total_attack`; override generic flags |
| Baselines & Deviations | 59–69 | Calculate 9 baselines from Lazy 5e, compute 7 deviations (using **totals**) |
| Phase 1: Baseline HP | 70–71 | Filter to valid HP, calculate resistance/immunity multipliers |
| Phase 2: CR Tiers + Penalties | 72–76 | Split into 5 CR tiers, apply `PHASE2_PENALTIES`, calculate scaled features |
| Combine & Save | 77–82 | Recombine tiers, select `columns_to_export`, save to parquet |

### Key data flow within the notebook

```
df  (raw 324 rows)
 ├── parse basic features → ac_value, highest_attack_bonus, estimated_dpr, ...
 ├── parse special traits → has_magic_resistance, has_advantage_condition, ...
 ├── merge spellcaster overrides → updates total_dpr, ac_value, etc.
 ├── DMG feature costing → feature_ac, feature_attack, total_ac, total_attack
 │                          (overrides has_advantage_condition → 0 where classified)
 ├── baselines from lazy_5e → ac_baseline, attack_baseline, dpr_baseline, ...
 ├── deviations = total_{stat} - baseline
 │
 ↓
df_valid  (324 rows with HP > 0)
 ├── Phase 1: hp_after_phase1 = hp_baseline
 ├── split into df_cr1 … df_cr5
 ├── Phase 2: hp_after_phase2 = hp_after_phase1 + Σ(deviation × penalty)
 ├── resistance/immunity penalty → hp_after_resist_immun_penalty
 ├── scaled features (legendary_resistance, regeneration) × hp_after_resist_immun_penalty
 ├── residual_hp = actual_hp - hp_after_resist_immun_penalty
 │
 ↓
df_engineered  (recombined 324 rows)
 └── saved to engineered_features.parquet
```

---

## helper_files/ Survey

All helper modules live in `notebooks/helper_files/`.
They are imported via the package (`from notebooks.helper_files import ...`
when running from project root, or `from helper_files import ...` when
running inside `notebooks/`).

### Module Dependency Graph

```
feature_config.py        (no internal deps — pure configuration)
        ↓
parsers.py               (imports EXPECTED_COMBAT_ROUNDS, DMG_AC_ADJUSTMENTS,
                           DMG_ATTACK_ADJUSTMENTS from feature_config)
        ↓
baseline_functions.py    (imports BASELINE_DATA, FLY_SPEED_BASELINE,
                           DARKVISION_BASELINE, GROUND_SPEED_BASELINE,
                           RESISTANCE_PENALTY_PER_COUNT, IMMUNITY_PENALTY_PER_COUNT,
                           get_cr_tier from feature_config)
        ↓
model_utils.py           (imports CONDITIONS, PHASE2_PENALTIES, get_cr_tier,
                           get_phase3_features, MODEL_CONFIG from feature_config)
        ↓
model_analysis.py        (imports CR_TIERS, PHASE2_FEATURES from feature_config)
```

### feature_config.py  — All configuration constants

This is the single source of truth for model configuration.
**Everything that needs manual curation lives here** (or in the notebook
cell-level overrides noted below).

| Constant | What it controls | When to edit |
|----------|-----------------|--------------|
| `EXPECTED_COMBAT_ROUNDS` | Burst damage amortisation (÷3) | If DMG combat-length assumption changes |
| `DMG_AC_ADJUSTMENTS` | DMG feature → effective AC bonus | When adding/removing a DMG AC feature |
| `DMG_ATTACK_ADJUSTMENTS` | DMG feature → effective attack bonus | When adding/removing a DMG attack feature |
| `DMG_ADVANTAGE_OVERRIDES` | Features that force `has_advantage_condition=0` | When a new DMG feature grants advantage |
| `DMG_ATTACKERS_ADVANTAGE_OVERRIDES` | Features that force `has_attackers_advantage=0` | When a new DMG feature grants attacker advantage |
| `CR_TIERS` | 5 CR tier boundaries | Unlikely to change |
| `CONDITIONS` | 10 D&D conditions → auto-generates `inflicts_{cond}` columns | When adding a trackable condition |
| `PHASE2_FEATURES` | 9 features with hand-tuned penalties | When adding/removing a Phase 2 penalty feature |
| `PHASE2_PENALTIES` | 5 × 9 penalty matrix (per-tier per-feature) | When tuning Phase 2 HP adjustments |
| `PHASE3_FEATURES_BASE` | 27 features with learned coefficients | When adding/removing a Phase 3 regression feature |
| `BASELINE_DATA` | 34 CR baseline data points (from Lazy 5e) | When source baseline data changes |
| `FLY_SPEED_BASELINE` | Fly speed baseline per tier | When adjusting fly-speed expectations |
| `DARKVISION_BASELINE` | Darkvision baseline per tier | When adjusting darkvision expectations |
| `RESISTANCE_PENALTY_PER_COUNT` | HP penalty % per resistance | When tuning Phase 1.5 |
| `IMMUNITY_PENALTY_PER_COUNT` | HP penalty % per immunity | When tuning Phase 1.5 |
| `MODEL_CONFIG` | Constrained features, min R², max coef | When changing model training constraints |
| `EXPORT_COLUMNS` | Columns in final CSV export | When any feature is added/removed (see checklist below) |

### parsers.py  — Parsing functions (raw data → numeric features)

34 functions. Key ones with **hardcoded logic** that may need updating:

| Function | Line (approx) | Manual curation notes |
|----------|--------------|----------------------|
| `parse_dmg_features(row)` | ~480 | Keyword matching for 12 DMG features — update when adding a new DMG feature |
| `has_advantage_condition(row)` | ~340 | Hardcoded keyword list for advantage detection |
| `has_disadvantage_condition(row)` | ~360 | Hardcoded keyword list for disadvantage detection |
| `has_attackers_advantage(row)` | ~380 | Hardcoded keyword list for attacker-advantage detection |
| `parse_charge_bonus_attack()` | ~415 | Burst damage keywords (charge, pounce, rampage) |

### baseline_functions.py  — CR-based interpolation

12 functions. All read from `BASELINE_DATA` in feature_config.py.
No hardcoded data inside this module.

### model_utils.py  — Model training / evaluation

14 functions. Reads `MODEL_CONFIG`, `get_phase3_features()`, `PHASE2_PENALTIES`.
Contains `ConstrainedModel` class and `train_constrained_model()`.

### model_analysis.py  — Visualisation and investigation

5 functions. Reads `CR_TIERS`, `PHASE2_FEATURES` for contribution breakdowns.

---

## Manually Curated Items in the Notebook

These values are defined **inside the notebook** rather than in helper_files:

| Cell | Variable | Purpose |
|------|----------|---------|
| 12 | `CONDITION_DEFINITIONS` | Reference text for each D&D condition (informational only; the actual list is `CONDITIONS` in feature_config.py) |
| 36 | `DC_OVERRIDES` | Per-creature save DC corrections for thematic abilities that shouldn't count as combat power |
| 50 | `spellcasting_rename_dict` | Column name mapping from spellcaster feature CSV to main df columns |
| 80 | `columns_to_export` | Export column list for this notebook's parquet output (see maintenance checklist below) |

---

## 4-Layer Column Convention

Combat stats follow a 4-layer structure. Deviations are always computed from
the **total** column.

| Layer | AC | Attack | DPR |
|-------|-----|--------|-----|
| **estimated** (parsed from stat block) | `ac_value` | `highest_attack_bonus` | `estimated_dpr` |
| **feature** (DMG trait adjustments) | `feature_ac` | `feature_attack` | `feature_dpr` |
| **legendary** | — | — | `legendary_dpr` |
| **total** (sum of above, used for deviation) | `total_ac` | `total_attack` | `total_dpr` |

`feature_dpr` specifically holds burst damage from charge/pounce/rampage,
amortised over `EXPECTED_COMBAT_ROUNDS` (3). Breath weapon damage is **not**
included — it lives in the `Desc` field rather than the `Damage` field, so
`parse_dpr_from_json()` already excludes it.

---

## Override Logic (preventing double-counting)

Generic flags like `has_advantage_condition` and `has_attackers_advantage`
detect whether a creature has *any* source of advantage. These are used as
Phase 2 penalty features.

When a **specific DMG feature** is detected (e.g. `feature_pack_tactics`),
the cost is already captured in `feature_attack` → `total_attack` →
`attack_deviation`. To prevent double-counting, the generic flag is forced
to 0.

Configuration lives in feature_config.py:
- `DMG_ADVANTAGE_OVERRIDES` → list of feature names that zero out `has_advantage_condition`
- `DMG_ATTACKERS_ADVANTAGE_OVERRIDES` → list of feature names that zero out `has_attackers_advantage`

After overrides, these generic flags mean: "has advantage from an
**unclassified** source (not yet mapped to a specific DMG feature)."

---

## Checklist: Adding / Removing a Feature

### Adding a new DMG feature (e.g. "Parry")
1. `feature_config.py`: Add to `DMG_AC_ADJUSTMENTS` or `DMG_ATTACK_ADJUSTMENTS`
2. `feature_config.py`: If it grants advantage, add to `DMG_ADVANTAGE_OVERRIDES` / `DMG_ATTACKERS_ADVANTAGE_OVERRIDES`
3. `parsers.py` → `parse_dmg_features()`: Add keyword detection logic
4. `feature_config.py` → `EXPORT_COLUMNS`: Add `feature_{name}`
5. `1_feature_engineering.ipynb` → cell 80 `columns_to_export`: Add `feature_{name}`

### Adding a new Phase 2 feature
1. `feature_config.py` → `PHASE2_FEATURES`: Add feature name
2. `feature_config.py` → `PHASE2_PENALTIES`: Add penalty value to all 5 tiers
3. Ensure the column is computed in `1_feature_engineering.ipynb` **before** Phase 2 (cells 70+)

### Adding a new Phase 3 feature
1. `feature_config.py` → `PHASE3_FEATURES_BASE`: Add feature name
2. If boolean (should have non-positive coeff): add to `MODEL_CONFIG['constrained_features']`
3. Ensure the column is computed in `1_feature_engineering.ipynb`

### Adding a new condition
1. `feature_config.py` → `CONDITIONS`: Add condition name
2. The `inflicts_{condition}` column is auto-generated in cell 44
3. It's auto-added to Phase 3 features via `get_phase3_features()`
4. It's auto-added to exports via `get_export_columns()`
5. Add to `columns_to_export` in cell 80 if you want it in the parquet output

### Removing a feature
1. Remove from all lists in `feature_config.py` (PHASE2_FEATURES, PHASE3_FEATURES_BASE, MODEL_CONFIG, EXPORT_COLUMNS)
2. Remove from `columns_to_export` in cell 80
3. Remove or comment out the computation in the notebook
4. If it was a DMG feature: remove from DMG dicts, `parse_dmg_features()`, and OVERRIDE lists

---

## Reference: data/dmg_monster_feature_costs.csv

Full DMG Monster Features table (pp.280-281) with 93 entries. Columns:
`monster_feature`, `example_monster`, `effect_on_challenge_rating`.

Not all entries are implemented as `feature_{name}` columns — only features
with AC/attack/damage costs AND creatures in our 324-monster dataset get
detection logic. Features with zero applicable creatures (e.g. Parry,
Superior Invisibility) are skipped.
