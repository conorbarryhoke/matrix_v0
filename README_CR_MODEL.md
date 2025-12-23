# D&D 5E Challenge Rating Prediction Model

A machine learning system to predict Challenge Rating (CR) for D&D 5E monsters based on their attributes, using a two-model approach optimized for different CR ranges.

## Project Structure

```
.
├── dnd5e_monsters_2014.csv          # Monster database (324 monsters)
├── cr_prediction_model.ipynb        # Main Jupyter notebook
├── requirements.txt                 # Python dependencies
├── README_CR_MODEL.md              # This file
└── (generated after running notebook)
    ├── low_cr_model.pkl             # Trained low CR classifier
    ├── standard_cr_model.pkl        # Trained standard CR regressor
    └── feature_columns.pkl          # Feature list for predictions
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Notebook

```bash
jupyter notebook cr_prediction_model.ipynb
```

Or if using VS Code, just open the notebook and run all cells.

### 3. Explore the Results

The notebook will:
- Load and analyze the monster dataset
- Engineer 60+ features from the raw data
- Train two separate models (low CR and standard CR)
- Show feature importance rankings
- Generate visualizations and performance metrics

## Two-Model Architecture

### Why Two Models?

Challenge Rating scales differently at low vs high levels:

**Low CR (≤1)**:
- Small stat changes matter enormously
- CR 1/4 to CR 1/2 is a 2× difficulty jump
- Simple creatures with basic stats
- **Approach**: 5-class classification (0, 1/8, 1/4, 1/2, 1)

**Standard CR (≥2)**:
- More continuous scaling
- Complex interactions between abilities
- Legendary actions, resistances become crucial
- **Approach**: Regression for continuous CR prediction

## Feature Engineering

The model creates ~60 features across several categories:

### Parsed Numeric Features
- HP (average, dice count, dice size)
- AC value
- Speed (ground, fly, swim, burrow, climb)

### Ability Scores
- All six modifiers (STR, DEX, CON, INT, WIS, CHA)
- Derived: total sum, physical sum, mental sum, highest/lowest

### Combat Metrics
- HP-to-AC ratio
- Effective HP (HP × (1 + AC/20))
- Save and skill proficiency counts

### Damage Type Coverage
- Resistance, immunity, vulnerability counts
- Condition immunity count

### Senses
- Darkvision presence and range
- Blindsight, truesight, tremorsense
- Passive perception

### Action Economy
- Counts of traits, actions, reactions, bonus actions
- Legendary action count and per-round usage
- Total ability count

### Attack Features
- Multiattack presence
- Highest attack bonus
- Highest save DC

### Special Abilities
- Legendary resistance
- Magic resistance
- Regeneration
- Spellcasting level

### Categorical
- Size (ordinal: Tiny=1 to Gargantuan=6)
- Type (one-hot encoded: aberration, beast, dragon, etc.)

## Model Performance

### Expected Results

**Low CR Model** (Classification):
- Target: 70%+ exact accuracy
- 90%+ within ±1 tier

**Standard CR Model** (Regression):
- Target: MAE < 2 CR points
- 80%+ predictions within ±2 CR

## Key Insights

The notebook reveals:

1. **HP and AC are fundamental** across all CR ranges
2. **Feature importance shifts by CR**:
   - Low CR: Basic stats dominate (HP, AC, attack bonus)
   - High CR: Special abilities matter (legendary actions, resistances)
3. **Action economy matters**: Legendary actions strongly predict high CR
4. **Defensive abilities scale**: Immunities/resistances more valuable at high CR

## Using the Trained Models

After running the notebook, you can load and use the models:

```python
import pickle
import pandas as pd

# Load models
with open('low_cr_model.pkl', 'rb') as f:
    low_cr_model = pickle.load(f)

with open('standard_cr_model.pkl', 'rb') as f:
    standard_cr_model = pickle.load(f)

with open('feature_columns.pkl', 'rb') as f:
    feature_columns = pickle.load(f)

# Create feature dict for your custom monster
custom_monster = {
    'hp_avg': 45,
    'ac_value': 15,
    'STR_Mod': 3,
    # ... (set all ~60 features)
}

# Convert to DataFrame
features_df = pd.DataFrame([custom_monster])[feature_columns]

# Predict CR
if features_df['hp_avg'].iloc[0] < 50:  # Simple routing logic
    predicted_cr = low_cr_model.predict(features_df)[0]
else:
    predicted_cr = standard_cr_model.predict(features_df)[0]

print(f"Predicted CR: {predicted_cr}")
```

## Feature Value Analysis

The feature importance scores directly answer "what is each feature worth in CR?"

For example, if the analysis shows:
- `has_legendary_actions`: importance 0.15
- `hp_avg`: importance 0.12
- `immunity_count`: importance 0.08

This tells you that legendary actions are the single most valuable feature for determining CR, followed by HP, then immunities.

You can use this to:
1. **Balance custom monsters**: Know which stats to adjust to hit target CR
2. **Value abilities**: Understand the "CR cost" of adding features
3. **Optimize designs**: Focus on high-impact features for your desired CR

## Next Steps

Potential extensions:
1. **Add NLP embeddings** for deeper text analysis of abilities
2. **Build inverse model**: Input desired CR, get suggested stat ranges
3. **Create web interface** for easy CR prediction
4. **Analyze CR budgeting**: "How much CR does legendary resistance cost?"
5. **Model interactions**: Capture synergies (e.g., flight + high AC)

## Data Source

- Dataset: 324 D&D 5E monsters from 2014 Free Basic Rules
- Source: Roll20 Compendium API
- Parsing script: `parse_monsters.py`

## License

For educational and personal use. D&D 5E content is copyright Wizards of the Coast.

## Contributing

This is a personal project for monster design tools. Feel free to extend or modify for your own use!
