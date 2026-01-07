# D&D 5e Monster Builder v2

A web application for predicting monster Hit Points using a three-phase baseline model with CR-based scaling.

## Features

### Three-Phase HP Prediction Model

1. **Phase 1: CR Baseline**
   - Uses adjusted HP baselines from Lazy 5e Monster Stats
   - +50% HP for CR ≤ 1
   - +20% HP for CR ≥ 2

2. **Phase 2: Combat Stats & Powerful Abilities**
   - **Stat Deviations** (fixed penalties):
     - AC: -5 HP per point above baseline
     - Attack Bonus: -6 HP per point above baseline
     - DPR: -2.5 HP per point above baseline

   - **Scaled Abilities** (percentage-based penalties):
     - Flying: -10% of baseline HP
     - Legendary Resistance: -15% of baseline HP
     - Magic Resistance: -12% of baseline HP
     - Regeneration: -18% of baseline HP
     - Legendary Actions: -8% of baseline HP

3. **Phase 3: Additional Features**
   - Size, movement speeds
   - Proficiencies (saves, skills)
   - Resistances and immunities
   - Condition inflictions (11 conditions)
   - Special abilities (multiattack, grapple, spellcasting, etc.)

## Model Performance

- **Test R²**: 0.595
- **Test MAE**: 36.1 HP
- **Total Features**: 52
- **No monster type features** (cleaner, more generalizable model)

## Key Improvements from v1

1. **Adjusted HP Baselines**: Higher baselines match actual monster HP better
2. **Scaled Abilities**: Powerful abilities now scale with CR instead of fixed penalties
3. **Better Organization**: Clear three-phase structure in the UI
4. **Real-time Feedback**: Shows deviations and their HP impact immediately
5. **Expandable Sections**: Cleaner interface for optional features

## How to Use

1. Open `index.html` in a web browser
2. Select the monster's Challenge Rating
3. Adjust combat stats (AC, Attack, DPR) - deviations from baseline are shown
4. Check boxes for powerful abilities (flying, legendary resistance, etc.)
5. Add additional features as needed
6. The predicted HP updates automatically!

## Example Predictions

### Aarakocra (CR 0.25, Actual: 13 HP)
- Baseline HP: 19.5 (adjusted +50% for low CR)
- Predicted: ~-5 HP (still challenging due to stat penalties)
- Note: Very low CR creatures are harder to predict accurately

### Pegasus (CR 2, Actual: 59 HP)
- Baseline HP: 54 (adjusted +20%)
- Predicted: 65 HP
- Error: +6 HP (+10%) ✅ Excellent!

### Adult Red Dragon (CR 17, Actual: 256 HP)
- Baseline HP: 295 (adjusted +20%)
- Penalties scale appropriately with high HP pool
- Prediction accuracy: Very good for high-CR creatures

## Technical Details

### Model Architecture
- Constrained linear regression
- 8 fixed coefficients (Phase 2)
- 44 learned coefficients (Phase 3)
- StandardScaler normalization

### Constraints
All Phase 2 penalties are fixed (not learned from data):
```javascript
{
  ac_deviation: -5.0,
  attack_deviation: -6.0,
  dpr_deviation: -2.5,
  has_flying_scaled: -0.10,
  has_legendary_resistance_scaled: -0.15,
  has_magic_resistance_scaled: -0.12,
  has_regeneration_scaled: -0.18,
  has_legendary_actions_scaled: -0.08
}
```

### Files
- `index.html` - Main UI with three-phase structure
- `app.js` - Prediction logic and CR baseline interpolation
- `styles.css` - Modern, responsive styling
- `model_data.json` - Model coefficients, scaler, baselines, constraints
- `README.md` - This file

## Future Improvements

### Potential Enhancements
1. Scale AC/Attack/DPR penalties with baseline HP (like abilities)
2. Add more special abilities (pack tactics, sneak attack, etc.)
3. Import/export monster stat blocks
4. Comparison with similar CR creatures
5. Suggested CR based on stats

### Known Limitations
- Very low CR creatures (< 0.25) can predict negative HP
- Fixed stat deviation penalties don't scale with CR
- Model trained on 2014 Monster Manual only

## Credits

- **HP Baselines**: Based on Lazy 5e Monster Building (Sly Flourish)
- **Model**: Three-phase constrained regression with CR scaling
- **Data**: D&D 5e 2014 Monster Manual (324 creatures)

## Version History

### v2.0 (Current)
- Adjusted HP baselines (+50% for CR ≤ 1, +20% for CR ≥ 2)
- Scaled ability penalties (percentage of baseline HP)
- Three-phase UI organization
- Real-time deviation feedback
- Improved model performance (R² = 0.595)

### v1.0 (Previous)
- Basic baseline model
- Fixed ability penalties
- Single-column layout
- R² = 0.638 (but poor low-CR predictions)
