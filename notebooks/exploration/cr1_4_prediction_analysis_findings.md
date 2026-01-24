# CR 1-4 Prediction Error Analysis Findings

## Overall Statistics

| Metric | Value |
|--------|-------|
| Total CR 1-4 monsters | 99 |
| Good predictions (<10% error) | 23 (23.2%) |
| Bad predictions (>=10% error) | 76 (76.8%) |
| Over-predictions | 54 (54.5%) |
| Under-predictions | 45 (45.5%) |
| Mean absolute error | 11.6 HP |
| Mean absolute % error | 28.1% |
| Median absolute % error | 22.2% |

---

## Part 1: Good vs Bad Predictions

### Engineered Features

Few statistically significant differences found:

| Feature | Good Mean | Bad Mean | Diff | p-value |
|---------|-----------|----------|------|---------|
| has_tremorsense | 0.04 | 0.00 | -0.04 | 0.073* |
| inflicts_petrified | 0.04 | 0.00 | -0.04 | 0.073* |

*Note: Most engineered features show no significant difference between good and bad predictions*

### Pattern Differences (Traits/Actions Text)

| Pattern | Good % | Bad % | Diff | Interpretation |
|---------|--------|-------|------|----------------|
| shapechange | 0.0% | 14.5% | +14.5% | Shapechanger mechanics not captured |
| true_form | 0.0% | 17.1% | +17.1% | Transformation not modeled |
| polymorph | 0.0% | 15.8% | +15.8% | Same issue |
| revert | 0.0% | 15.8% | +15.8% | Same issue |
| multiattack | 26.1% | 36.8% | +10.8% | Complex attack patterns = worse predictions |
| spellcasting_ref | 0.0% | 9.2% | +9.2% | Spellcasting complexity not fully captured |
| damage_reduction | 0.0% | 9.2% | +9.2% | DR mechanics not modeled |
| special_action | 8.7% | 17.1% | +8.4% | Special action economy not captured |

---

## Part 2: Over-predictions vs Under-predictions

### Highly Significant Engineered Feature Differences

| Feature | Over-pred Mean | Under-pred Mean | Diff | p-value |
|---------|----------------|-----------------|------|---------|
| save_dc_deviation | -0.63 | +0.40 | -1.03 | 0.0000*** |
| actual_hp | 42.1 | 57.8 | -15.7 | 0.0003*** |
| attack_deviation | -0.30 | +0.13 | -0.43 | 0.016** |
| highest_attack_bonus | 4.83 | 5.27 | -0.43 | 0.017** |
| estimated_dpr | 13.0 | 16.1 | -3.14 | 0.030** |
| resistance_count | 1.09 | 0.27 | +0.83 | 0.074* |

**Interpretations:**
- **Higher save DC** -> under-predicted (more HP than expected)
- **Low-HP monsters** -> systematically over-predicted
- **Higher attack/DPR** -> under-predicted (offensive power justifies HP)
- **More resistances** -> over-predicted (resistance penalty may be too weak)

### Pattern Differences by Prediction Direction

**Patterns more common in OVER-predictions (monster has LESS HP than expected):**

| Pattern | Over % | Under % | Diff |
|---------|--------|---------|------|
| regains_hp | 11.1% | 2.2% | +8.9% |
| shapechange | 14.8% | 6.7% | +8.1% |
| incapacitate_ref | 16.7% | 8.9% | +7.8% |
| repeat_save | 22.2% | 13.3% | +8.9% |
| failed_save_effect | 27.8% | 20.0% | +7.8% |

*Interpretation: These abilities already "pay for" themselves via HP reduction*

**Patterns more common in UNDER-predictions (monster has MORE HP than expected):**

| Pattern | Over % | Under % | Diff |
|---------|--------|---------|------|
| prone_ref | 9.3% | 20.0% | -10.7% |
| grapple_ref | 5.6% | 13.3% | -7.8% |
| restrain_ref | 5.6% | 13.3% | -7.8% |
| escape_dc | 5.6% | 13.3% | -7.8% |

*Interpretation: Control abilities may justify higher HP*

---

## Worst Predictions Analysis

### Top 10 Over-predictions (Model Expects MORE HP Than Actual)

| Monster | CR | Actual HP | Predicted HP | Error |
|---------|-----|-----------|--------------|-------|
| Quasit | 1 | 7 | 18.9 | +169.6% |
| Hippogriff | 1 | 19 | 40.1 | +111.1% |
| Phase Spider | 3 | 32 | 63.6 | +98.7% |
| Imp | 1 | 10 | 0.9 | -91.0% |
| Giant Vulture | 1 | 22 | 40.7 | +85.1% |
| Ghoul | 1 | 22 | 38.6 | +75.6% |
| Wererat | 2 | 33 | 57.4 | +74.0% |
| Animated Armor | 1 | 33 | 10.4 | -68.4% |
| Black Dragon Wyrmling | 2 | 33 | 53.8 | +63.0% |
| Giant Spider | 1 | 26 | 12.1 | -53.4% |

**Common Characteristics:**
- Shapechangers (Quasit, Wererat)
- Ethereal/escape abilities (Phase Spider, Quasit)
- Flying mounts with low threat (Hippogriff, Giant Vulture)
- Creatures that trade HP for special abilities

### Top 10 Under-predictions (Model Expects LESS HP Than Actual)

| Monster | CR | Actual HP | Predicted HP | Error |
|---------|-----|-----------|--------------|-------|
| Couatl | 4 | 97 | 64.0 | -34.0% |
| Weretiger | 4 | 120 | 87.7 | -26.9% |
| Ogre Zombie | 2 | 85 | 55.6 | -34.6% |
| Green Hag | 3 | 82 | 55.9 | -31.8% |
| Gargoyle | 2 | 52 | 27.7 | -46.8% |
| Gibbering Mouther | 2 | 67 | 43.6 | -35.0% |
| Chuul | 4 | 93 | 70.1 | -24.6% |
| Animated Armor | 1 | 33 | 10.4 | -68.4% |
| Winter Wolf | 3 | 75 | 52.7 | -29.8% |
| Mimic | 2 | 58 | 36.0 | -38.0% |

**Common Characteristics:**
- Very high AC (Couatl AC 19, Gargoyle immunities)
- "Tank" builds with low offense but high HP (Ogre Zombie, Animated Armor)
- Control/grapple abilities (Chuul, Mimic)
- Resistance/immunity stacking

---

## Best Predictions (For Reference)

| Monster | CR | Actual HP | Predicted HP | Error |
|---------|-----|-----------|--------------|-------|
| Basilisk | 3 | 52 | 52.0 | +0.0% |
| Ankheg | 2 | 39 | 38.9 | -0.1% |
| Ogre | 2 | 59 | 59.3 | +0.5% |
| Harpy | 1 | 38 | 38.5 | +1.3% |
| Rhinoceros | 2 | 45 | 44.2 | -1.8% |
| Tiger | 1 | 37 | 37.9 | +2.4% |
| Ettin | 4 | 85 | 82.8 | -2.6% |

**Common Characteristics:**
- "Straightforward" monsters with balanced stats
- Primarily physical attackers
- No complex transformation or escape mechanics

---

## Recommendations for Model Improvement

### 1. Add Shapechanger/Transformation Feature
**Priority: HIGH**

Creatures with shapechange, polymorph, revert, or true_form patterns consistently have LESS HP than expected. Their versatility/escape ability is already "paid for" via HP reduction.

**Suggested Implementation:**
- Add `has_shapechange` feature
- Apply negative HP adjustment (these creatures should have lower predicted HP)

### 2. Add Control Ability Features
**Priority: HIGH**

Creatures with grapple, restrain, and escape_dc patterns have MORE HP than expected. Control abilities justify tankiness.

**Suggested Implementation:**
- Add `has_grapple_control` feature (grapple + restrain + escape_dc)
- Apply positive HP adjustment

### 3. Re-examine Resistance Penalty at CR 1-4
**Priority: MEDIUM**

Creatures with high resistance counts are over-predicted (resistance_count significantly higher in over-predictions at p=0.074). The resistance penalty may be too weak at lower CRs.

### 4. Add Damage Reduction Feature
**Priority: MEDIUM**

`damage_reduction` pattern appears in 9.2% of bad predictions vs 0% of good. This mechanic is not currently modeled.

### 5. Address Low-HP Monster Bias
**Priority: MEDIUM**

Low-HP monsters (actual_hp mean 42 in over-pred vs 58 in under-pred) are systematically over-predicted. The model struggles with creatures that heavily trade HP for special abilities.

**Possible approaches:**
- Add a "glass cannon" or "special ability density" feature
- Cap minimum predicted HP based on CR

### 6. Consider Ethereal/Escape Mechanics
**Priority: LOW**

Phase Spider (+99% error) and Quasit (+170% error) both have ethereal escape. These should have reduced HP expectations similar to shapechangers.

---

## Part 3: Archetype Analysis

### Archetype Distribution in CR 1-4

| Archetype | Count | % of CR 1-4 |
|-----------|-------|-------------|
| brute | 53 | 53.5% |
| tank | 45 | 45.5% |
| skirmisher | 41 | 41.4% |
| lieutenant | 26 | 26.3% |
| solo_challenge | 21 | 21.2% |
| controller | 20 | 20.2% |
| ambusher | 13 | 13.1% |
| boss | 9 | 9.1% |
| minion | 8 | 8.1% |
| spellcaster | 7 | 7.1% |
| swarm | 2 | 2.0% |
| enhanced_version | 1 | 1.0% |

### Archetype Scores: Over vs Under Predictions (Statistically Significant)

| Archetype | Over-pred Mean | Under-pred Mean | Diff | p-value |
|-----------|----------------|-----------------|------|---------|
| tank | 0.185 | 0.322 | -0.137 | 0.012** |
| brute | 0.261 | 0.347 | -0.086 | 0.033** |
| controller | 0.124 | 0.187 | -0.063 | 0.093* |

**Key Finding:** Tank, Brute, and Controller archetypes are significantly associated with **under-prediction** - these creatures have MORE HP than the model expects.

### Prediction Accuracy by Archetype Label

| Archetype Label | Count | Good % | Avg Error | Avg % Error |
|-----------------|-------|--------|-----------|-------------|
| Boss | 9 | 11.1% | 8.0 HP | 17.8% |
| Solo Challenge | 21 | 33.3% | 9.9 HP | 23.5% |
| Tank | 45 | 24.4% | 12.7 HP | 26.3% |
| Skirmisher | 41 | 24.4% | 10.5 HP | 27.6% |
| Brute | 53 | 24.5% | 12.1 HP | 29.9% |
| Minion | 8 | 12.5% | 11.8 HP | 31.3% |
| Controller | 20 | 25.0% | 12.4 HP | 32.0% |
| Standard | 9 | 22.2% | 17.7 HP | 32.0% |
| Spellcaster | 7 | 0.0% | 16.2 HP | 32.1% |
| Lieutenant | 26 | 15.4% | 12.4 HP | 34.9% |
| Ambusher | 13 | 15.4% | 11.8 HP | 38.8% |

**Key Findings:**
- **Boss** monsters are best predicted (17.8% avg error)
- **Solo Challenge** monsters have highest good prediction rate (33.3%)
- **Spellcasters** are never well-predicted (0% good rate)
- **Ambushers** have highest average error (38.8%)

### Archetype Score Correlations with Prediction Error

| Archetype | Corr w/ |Error| | Corr w/ Signed Error | Interpretation |
|-----------|------------------|----------------------|----------------|
| ambusher | +0.159 | -0.044 | Harder to predict, slight under-pred |
| lieutenant | +0.147 | +0.067 | Harder to predict, slight over-pred |
| tank | -0.032 | **-0.236** | Strongly under-predicted |
| controller | +0.044 | **-0.127** | Under-predicted |
| spellcaster | +0.041 | **-0.115** | Under-predicted |
| minion | +0.037 | **+0.112** | Over-predicted |
| brute | -0.010 | -0.081 | Under-predicted |

### Archetype Analysis Summary

**1. Archetypes with Higher Error (harder to predict):**
- Ambusher: r=+0.159 with |error|
- Lieutenant: r=+0.147 with |error|

**2. Archetypes with Lower Error (easier to predict):**
- Solo Challenge: r=-0.080 with |error|
- Enhanced Version: r=-0.053 with |error|

**3. Archetypes Associated with OVER-prediction (model expects MORE HP):**
- Minion: r=+0.112 (creatures designed to be weaker, HP already reduced)
- Swarm: r=+0.091
- Lieutenant: r=+0.067

**4. Archetypes Associated with UNDER-prediction (model expects LESS HP):**
- **Tank: r=-0.236** (strong signal - tanks have more HP than expected)
- Controller: r=-0.127
- Spellcaster: r=-0.115
- Brute: r=-0.081

---

## Updated Recommendations for Model Improvement

### 1. Add Shapechanger/Transformation Feature
**Priority: HIGH**

Creatures with shapechange, polymorph, revert, or true_form patterns consistently have LESS HP than expected. Their versatility/escape ability is already "paid for" via HP reduction.

**Suggested Implementation:**
- Add `has_shapechange` feature
- Apply negative HP adjustment (these creatures should have lower predicted HP)

### 2. Adjust Tank Archetype Handling
**Priority: HIGH** (NEW)

Tank archetype has strong correlation (r=-0.236) with under-prediction. These creatures consistently have MORE HP than the model predicts.

**Suggested Implementation:**
- Consider tank_score as a Phase 2 or Phase 3 feature
- Positive HP adjustment for high tank scores

### 3. Add Control Ability Features
**Priority: HIGH**

Creatures with grapple, restrain, and escape_dc patterns have MORE HP than expected. Controller archetype (r=-0.127) confirms this pattern.

**Suggested Implementation:**
- Add `has_grapple_control` feature (grapple + restrain + escape_dc)
- Apply positive HP adjustment

### 4. Address Spellcaster Predictions
**Priority: HIGH** (NEW)

Spellcasters have 0% good prediction rate and are consistently under-predicted (r=-0.115). The model underestimates HP for spellcasting creatures.

**Suggested Implementation:**
- Review spellcaster_level penalty - may be too harsh
- Consider spellcaster_score as additional feature

### 5. Re-examine Resistance Penalty at CR 1-4
**Priority: MEDIUM**

Creatures with high resistance counts are over-predicted (resistance_count significantly higher in over-predictions at p=0.074). The resistance penalty may be too weak at lower CRs.

### 6. Address Minion Over-prediction
**Priority: MEDIUM** (NEW)

Minions are over-predicted (r=+0.112) - the model expects more HP than they have. These creatures are designed to be weaker.

**Suggested Implementation:**
- Consider minion_score as a negative HP adjustment

### 7. Add Damage Reduction Feature
**Priority: MEDIUM**

`damage_reduction` pattern appears in 9.2% of bad predictions vs 0% of good. This mechanic is not currently modeled.

### 8. Address Low-HP Monster Bias
**Priority: MEDIUM**

Low-HP monsters (actual_hp mean 42 in over-pred vs 58 in under-pred) are systematically over-predicted. The model struggles with creatures that heavily trade HP for special abilities.

---

## Summary Table: Patterns to Consider for New Features

| Pattern/Archetype | Prevalence | Direction | Suggested Action |
|-------------------|------------|-----------|------------------|
| **tank_score** | 45.5% of CR 1-4 | Under-predicted | Add as positive HP feature |
| shapechange/polymorph/revert | 15% of bad pred | Over-predicted | Add feature, reduce HP |
| **spellcaster_score** | 7.1% of CR 1-4 | Under-predicted | Review penalty, may be too harsh |
| **controller_score** | 20.2% of CR 1-4 | Under-predicted | Add as positive HP feature |
| grapple/restrain/escape_dc | 13% of under-pred | Under-predicted | Add feature, increase HP |
| **minion_score** | 8.1% of CR 1-4 | Over-predicted | Add as negative HP feature |
| damage_reduction | 9% of bad pred | Mixed | Add feature |
| regains_hp | 11% of over-pred | Over-predicted | May already be handled |
| ethereal/phase | Rare but extreme | Over-predicted | Consider as escape ability |
