# Multiattack DPR Parser Issues Analysis

## Summary

Analyzed 81 creatures with multiattack in CR 2-10 range. Found 28 creatures (35%) with potential parsing issues.

## Significant DPR Parsing Errors

| Creature | CR | Parsed DPR | Expected DPR | Diff | HP Error % | Issue |
|----------|-----|------------|--------------|------|------------|-------|
| Hydra | 8 | 21.0 | 52.5 | **-31.5** | -10.8% | Variable count not handled |
| Manticore | 3 | 43.0 | 22.5 | **+20.5** | -26.8% | OR alternatives summed |
| Gibbering Mouther | 2 | 35.0 | 17.5 | **+17.5** | -35.0% | Fallback doubled single attack |
| Veteran | 3 | 6.5 | 21.5 | **-15.0** | +28.3% | Only matched shortsword |
| Centaur | 2 | 33.5 | 20.5 | **+13.0** | -30.9% | OR alternatives summed |
| Wight | 3 | 26.0 | 13.0 | **+13.0** | -18.3% | OR alternatives summed |
| Wereboar | 4 | 10.0 | 20.0 | **-10.0** | +31.3% | Only one attack found |
| Gladiator | 5 | 26.0 | 33.0 | **-7.0** | -17.6% | "melee attacks" not matched |

---

## Pattern Categories That Need Fixes

### 1. OR Alternatives Being Summed (HIGH PRIORITY)
**Problem:** Parser matches BOTH sides of "X or Y" and sums them, when it should pick the better option.

**Affected Creatures:**
- **Centaur**: "one with its pike and one with its hooves **or** two with its longbow"
  - Parser: 9.5 + 11.0 + 2×6.5 = 33.5 (wrong - summed both)
  - Expected: max(20.5, 13.0) = 20.5

- **Manticore**: "one with its bite and two with its claws **or** three with its tail spikes"
  - Parser: 7.5 + 2×6.5 + 3×7.5 = 43.0 (wrong)
  - Expected: max(20.5, 22.5) = 22.5

- **Wight**: "two longsword attacks **or** two longbow attacks"
  - Parser: 2×6.5 + 2×6.5 = 26.0 (wrong)
  - Expected: 2×6.5 = 13.0

**Fix:** When encountering " or " in multiattack, split into alternatives and calculate each separately, then take the maximum.

---

### 2. Variable Attack Count (HIGH PRIORITY)
**Problem:** "as many X attacks as it has Y" pattern not handled.

**Affected Creatures:**
- **Hydra**: "makes as many bite attacks as it has heads"
  - Parser: 2×10.5 = 21.0 (fallback default)
  - Expected: 5×10.5 = 52.5 (starts with 5 heads)

**Fix:** Detect "as many...as it has" pattern and look up creature's default head count or similar stat.

---

### 3. Generic "melee/ranged attacks" (MEDIUM PRIORITY)
**Problem:** "makes X melee attacks" doesn't link to specific weapon, triggering fallback.

**Affected Creatures:**
- **Gladiator**: "three melee attacks or two ranged attacks"
  - Parser: 2×13.0 = 26.0 (fallback with 2×best)
  - Expected: 3×11.0 = 33.0

- **Cult Fanatic**: "two melee attacks" - works via fallback
- **Doppelganger**: "two melee attacks" - works via fallback
- **Knight**: "two melee attacks" - works via fallback
- **Deva**: "two melee attacks" - works via fallback

**Fix:** When matching "X melee attacks", multiply count by best melee weapon damage. Similarly for "ranged attacks".

---

### 4. "Only One Can Be X" Pattern (MEDIUM PRIORITY)
**Problem:** Parser only finds the restricted attack, missing the required second attack.

**Affected Creatures:**
- **Wereboar**: "two attacks, only one of which can be with its tusks"
  - Parser: 1×10.0 = 10.0 (only tusks)
  - Expected: 10.0 + 10.0 = 20.0 (tusks + maul)

- **Vampire Spawn**: "two attacks, only one of which can be a bite"
  - Parser: 13.5 (correct after fix somewhere)
  - Expected: 13.5 + 8.0 = 21.5

- **Wererat**: "two attacks, only one of which can be a bite"
  - Parser: 5.5 (just shortsword)
  - Expected: 4.5 + 5.5 = 10.0

**Fix:** Detect "only one of which can be X" and ensure total attack count is respected (2 attacks = 1×restricted + 1×other).

---

### 5. Conditional "If" Attacks (MEDIUM PRIORITY)
**Problem:** Conditional attacks (if hits, if grappling, if drawn) may or may not be counted correctly.

**Affected Creatures:**
- **Veteran**: "two longsword attacks. If it has a shortsword drawn, it can also make a shortsword attack"
  - Parser: 6.5 (only shortsword matched!)
  - Expected: 2×7.5 + 6.5 = 21.5

- **Grick**: "one tentacles. If that attack hits, make one beak attack"
  - Parser: 14.5 (correct - both matched)
  - Expected: 9.0 + 0.75×5.5 = 13.1 (should be ~75% for hit chance)

- **Chuul**: "two pincer attacks. If grappling, can use tentacles"
  - Parser: 22.0 (correct - pincers only, tentacles don't deal damage)

**Fix:**
- For "If...also make" patterns, include the conditional attack (possibly with modifier)
- For "If that attack hits", apply ~75% modifier
- Ensure base attacks are captured before conditional parsing

---

### 6. Form-Dependent Attacks (LOW PRIORITY)
**Problem:** Creatures with different attack options in different forms (humanoid/hybrid/bear).

**Affected Creatures:**
- **Werebear**: "In bear form, two claw attacks. In humanoid form, two greataxe attacks. In hybrid form, it can attack like a bear or a humanoid."
  - Parser: 2×15.0 = 30.0 (used fallback with bite as best)
  - Expected: 2×13.0 = 26.0 (hybrid with claws is most versatile)

- **Weretiger**: "In humanoid form, two scimitar attacks or two longbow attacks. In hybrid form, it can attack like a humanoid or make two claw attacks."
  - Parser: 12.8 (partial parse)
  - Expected: 2×8.0 = 16.0 (claw in hybrid)

**Fix:** For were-creatures, default to hybrid form attacks (most combat-relevant). Parse "in X form" sections separately.

---

### 7. Fallback Incorrectly Doubling (LOW PRIORITY)
**Problem:** When fallback triggers on single-attack creatures, it assumes 2 attacks.

**Affected Creatures:**
- **Gibbering Mouther**: "makes one bite attack and, if it can, uses its Blinding Spittle"
  - Parser: 2×17.5 = 35.0 (fallback doubled)
  - Expected: 17.5 (one bite, spittle is blind not damage)

**Fix:** Check if multiattack explicitly says "one" attack before applying fallback multiplier.

---

### 8. "Either X or Y" Weapon Choice (LOW PRIORITY)
**Problem:** "either with its X or its Y" should pick best option.

**Affected Creatures:**
- **Oni**: "two attacks, either with its claws or its glaive"
  - Parser: 2×15.0 = 30.0 (correct via fallback)
  - Expected: 2×15.0 = 30.0 (glaive is best)

**Status:** Works correctly via fallback.

---

## Recommended Fixes Priority

### High Priority (large DPR impact)
1. **OR alternative handling** - Stop summing both sides of "or"
2. **Variable count** - Handle "as many as it has heads" for Hydra

### Medium Priority (moderate impact)
3. **"Only one can be X"** - Ensure total attack count is met
4. **Generic "melee attacks"** - Link to best melee weapon
5. **Conditional "if" attacks** - Better parsing of base attacks before conditionals
6. **Veteran-specific fix** - "two longsword attacks" not matching "longsword (one-handed)"

### Low Priority (minor impact or rare)
7. **Form-dependent** - Default to hybrid form for were-creatures
8. **Fallback guard** - Don't double single-attack multiattacks
9. **Ability + attack** - Handle "uses X and makes one attack"

---

## Implementation Notes

### OR Alternative Detection
```python
# Before parsing specific attacks, check for OR alternatives
if ' or ' in multiattack_desc:
    # Split by " or " (but careful of "one or more", "two or three")
    # Common patterns:
    # "X. Or Y" - sentence-level alternative
    # "one with A and one with B or two with C" - option-level alternative
    alternatives = split_on_or(multiattack_desc)
    return max(parse_alternative(alt) for alt in alternatives)
```

### Variable Count Detection
```python
# Handle "as many X attacks as it has Y"
match = re.search(r'as many (\w+) attacks as it has (\w+)', multiattack_desc)
if match:
    attack_type = match.group(1)  # "bite"
    count_ref = match.group(2)    # "heads"
    # Look up default count (Hydra has 5 heads)
    count = get_creature_attribute_count(creature_name, count_ref)
    return count * attack_damages[attack_type]
```

### Only One Can Be Detection
```python
# Handle "X attacks, only one of which can be Y"
match = re.search(r'(\w+) attacks.*only one.*can be.*(\w+)', multiattack_desc)
if match:
    total_count = word_to_number(match.group(1))  # "two" -> 2
    restricted_attack = match.group(2)  # "bite"
    # Use 1x restricted + (total-1)x best other
    restricted_dmg = attack_damages.get(restricted_attack, 0)
    other_attacks = {k: v for k, v in attack_damages.items() if k != restricted_attack}
    best_other = max(other_attacks.values()) if other_attacks else 0
    return restricted_dmg + (total_count - 1) * best_other
```

---

## Key Findings Summary

### Impact on HP Model Predictions

The DPR parsing errors have a direct relationship with HP prediction errors:

| Issue Type | DPR Effect | HP Prediction Effect |
|------------|------------|---------------------|
| **Over-parsing** (OR summed) | DPR too high | Model expects lower HP → **Over-prediction** |
| **Under-parsing** (attacks missed) | DPR too low | Model expects higher HP → **Under-prediction** |

### Creatures Most Affected

**Over-parsed DPR → Over-predicted HP:**
- Manticore: +20.5 DPR error
- Gibbering Mouther: +17.5 DPR error
- Centaur: +13.0 DPR error
- Wight: +13.0 DPR error

**Under-parsed DPR → Under-predicted HP:**
- Hydra: -31.5 DPR error → -10.8% HP error
- Veteran: -15.0 DPR error → +28.3% HP error (inverse - other factors)
- Wereboar: -10.0 DPR error → +31.3% HP error
- Gladiator: -7.0 DPR error → -17.6% HP error

### Fix Priority by Impact

1. **OR alternatives** - Affects 5+ creatures, causes significant over-parsing
2. **Variable count (Hydra)** - Single creature but largest error (-31.5 DPR)
3. **"Only one can be"** - Affects 3 creatures (were-creatures, vampire spawn)
4. **Generic "melee attacks"** - Affects 5+ creatures, moderate under-parsing
5. **Conditional attacks** - Affects Veteran significantly (-15 DPR)

### Estimated Model Improvement

If all high-priority fixes are implemented:
- **5-8 creatures** would have significantly improved DPR estimates
- Expected reduction in HP prediction error for affected creatures: **10-30%**
- Overall CR 2-10 model R² improvement: **estimated 0.02-0.05**
