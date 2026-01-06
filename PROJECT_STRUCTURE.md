# Project Structure

This document outlines the organization of the Monster HP Prediction project.

## Directory Structure

```
matrix_v0/
├── data/                                    # Raw data files
│   ├── dnd5e_monsters_2014.csv             # Monster dataset (324 monsters)
│   ├── monsters_data.json                   # Parsed monster data
│   └── condition_analysis_results.json      # Condition impact analysis
│
├── pickled_models/                          # Trained ML models
│   ├── hp_lr_model_with_conditions.pkl      # Constrained HP model (88 features)
│   ├── hp_scaler_with_conditions.pkl        # Feature scaler for conditions model
│   ├── hp_feature_columns_with_conditions.pkl # Feature list for conditions model
│   ├── hp_lr_model_with_grapple.pkl         # HP model with grapple feature
│   ├── hp_scaler_with_grapple.pkl           # Scaler for grapple model
│   ├── hp_feature_columns_with_grapple.pkl  # Features for grapple model
│   ├── hp_lr_model.pkl                      # Original HP model
│   ├── hp_scaler.pkl                        # Original scaler
│   ├── hp_feature_columns.pkl               # Original features
│   ├── hp_rf_model.pkl                      # Random Forest HP model
│   ├── standard_cr_model.pkl                # CR prediction model
│   ├── low_cr_model.pkl                     # Low CR specialized model
│   └── feature_columns.pkl                  # General feature list
│
├── notebooks/                               # Jupyter notebooks
│   ├── hp_prediction_model_executed.ipynb   # Executed HP model training
│   ├── hp_prediction_model.ipynb            # HP model development
│   └── cr_prediction_model.ipynb            # CR model development
│
├── monster-builder-app/                     # Web application
│   ├── index.html                           # Main UI
│   ├── app.js                               # ML prediction logic
│   ├── styles.css                           # Styling
│   ├── model_data_with_conditions.json      # Model export (88 features)
│   ├── model_data.json                      # Current model data
│   ├── model_data_with_grapple.json         # Grapple model export
│   ├── model_data_original.json             # Original model backup
│   ├── README.md                            # App documentation
│   ├── DEPLOYMENT.md                        # Deployment guide
│   ├── QUICKSTART.md                        # Quick start guide
│   └── FILES.txt                            # File manifest
│
├── Python Scripts (Feature Engineering)
│   ├── constrained_condition_model.py       # Constrained regression training
│   ├── condition_feature_engineering.py     # Condition feature creation
│   ├── predict_aarakocra.py                 # Example prediction script
│   └── parse_monsters.py                    # Monster data parsing
│
├── Documentation
│   ├── PROJECT_STRUCTURE.md                 # This file
│   ├── GITHUB_PAGES_SETUP.md                # Deployment instructions
│   ├── index.html                           # Landing page
│   └── monsters_list.html                   # D&D monsters compendium
│
└── Configuration
    ├── .gitignore
    ├── .devcontainer/
    ├── .vscode/
    └── .claude/
```

## Model Evolution

### Version 1: Original HP Model
- **File**: `pickled_models/hp_lr_model.pkl`
- **Features**: 74 base features
- **Performance**: R² = 0.8627

### Version 2: Grapple Feature Added
- **File**: `pickled_models/hp_lr_model_with_grapple.pkl`
- **Features**: 75 (added `has_grapple`)
- **Impact**: +15.9 HP for grapple ability
- **Performance**: R² = 0.8551

### Version 3: Conditions Model (Current)
- **File**: `pickled_models/hp_lr_model_with_conditions.pkl`
- **Features**: 88 (added 11 condition features + has_flying + estimated_dpr)
- **Constrained Coefficients**:
  - `estimated_dpr`: -2.5
  - `ac_value`: -5.0
  - `highest_attack_bonus`: -6.0
  - `has_flying`: -7.0
- **Performance**: R² = 0.6036, MAE = 34.60 HP
- **Note**: Optimized for CR 3+ creatures

## Feature Categories

### Core Features (39)
- CR, AC, Size
- Speed (ground, fly, swim, burrow, climb)
- Attack bonus, Save DC, DPR
- Proficiencies, senses, passive perception
- Action economy (traits, actions, reactions, legendary actions)
- Special abilities (multiattack, legendary resistance, magic resistance, etc.)

### Condition Features (11)
- inflicts_poisoned, inflicts_blinded, inflicts_charmed
- inflicts_deafened, inflicts_frightened, inflicts_incapacitated
- inflicts_paralyzed, inflicts_petrified, inflicts_prone
- inflicts_restrained, inflicts_stunned

### Type Features (36)
- One-hot encoded monster types (humanoid, beast, dragon, etc.)

### Special Features (2)
- has_grapple
- has_flying

## Web Application

The Monster Builder app provides:
- Real-time HP prediction with 88 features
- Visual stat block generation
- Condition checkboxes with automatic HP adjustments
- DMG baseline comparison
- GitHub Pages deployment ready

**URL**: `https://conorbarryhoke.github.io/matrix_v0/monster-builder-app/`

## Usage

### Training New Models

```bash
# Train condition model with constraints
python constrained_condition_model.py

# Train unconstrained condition model
python condition_feature_engineering.py
```

### Making Predictions

```bash
# Example: Predict Aarakocra HP
python predict_aarakocra.py
```

### Running Web App Locally

```bash
cd monster-builder-app
python -m http.server 8000
# Visit http://localhost:8000
```

## Data Sources

- **D&D 5e Monsters Dataset**: 324 official monsters from 2014 rules
- **Features**: Manually engineered from monster stat blocks
- **Format**: CSV with 42 columns including abilities, traits, actions

## Notes

- All pickle files use the custom `ConstrainedLinearModel` class
- Model paths updated to use new folder structure
- Web app uses JSON exports, not pickle files
- Constrained model works best for CR 3+ creatures
