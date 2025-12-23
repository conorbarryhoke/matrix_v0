# D&D 5E Monster CR Prediction Project

A machine learning system for predicting Challenge Rating (CR) in D&D 5th Edition, with tools for custom monster creation and balancing.

## 🎯 Project Goal

Build a model that predicts CR for D&D 5E monsters and identifies the **value of each independent feature** to enable:
- Custom monster creation with target CR
- Monster balancing and adjustment
- Understanding which attributes contribute most to CR

## 📁 Project Structure

```
matrix_v0/
├── 📊 Data Files
│   ├── monsters_data.json              # Raw Roll20 API data (1.4MB)
│   ├── dnd5e_monsters_2014.csv        # Parsed monster database (324 monsters)
│   └── monsters_list.html             # Original HTML download
│
├── 🐍 Python Scripts
│   └── parse_monsters.py              # JSON to CSV parser
│
├── 📓 Jupyter Notebooks
│   └── cr_prediction_model.ipynb      # Main CR prediction model
│
├── 📚 Documentation
│   ├── README.md                       # This file
│   ├── README_MONSTERS.md             # Monster database docs
│   ├── README_CR_MODEL.md             # CR model docs
│   └── CONTEXT.md                     # Project context
│
├── ⚙️ Configuration
│   ├── requirements.txt               # Python dependencies
│   ├── setup.sh                       # Environment setup script
│   ├── .gitignore                     # Git ignore rules
│   ├── .vscode/
│   │   ├── settings.json              # VS Code workspace settings
│   │   └── extensions.json            # Recommended extensions
│   └── .devcontainer/
│       └── devcontainer.json          # Codespace configuration
│
└── 🤖 Generated Models (after running notebook)
    ├── low_cr_model.pkl               # Classifier for CR ≤ 1
    ├── standard_cr_model.pkl          # Regressor for CR ≥ 2
    └── feature_columns.pkl            # Feature list
```

## 🚀 Quick Start

### First Time Setup

When you open this Codespace for the first time:

```bash
# Run the setup script
./setup.sh
```

This will:
- Install all Python dependencies
- Verify data files are present
- Check notebook is ready

### Running the CR Prediction Model

1. **Open the notebook**: Click on `cr_prediction_model.ipynb` in VS Code
2. **Select Python kernel**: When prompted, choose the Python 3.x kernel
3. **Run all cells**: Click "Run All" or run cells individually
4. **Explore results**: View feature importance, model performance, and predictions

### Quick Commands

```bash
# Install/update dependencies
pip install -r requirements.txt

# Re-parse monster data (if needed)
python3 parse_monsters.py

# Launch Jupyter (alternative to VS Code notebook interface)
jupyter notebook
```

## 📊 Dataset

**Source**: Roll20 D&D 5E Compendium (2014 Free Basic Rules)

**Size**: 324 monsters with 43 attributes each

**Key Attributes**:
- Basic stats: Name, Size, Type, Alignment, AC, HP, Speed, CR, XP
- Ability scores: STR, DEX, CON, INT, WIS, CHA (with modifiers)
- Skills & saves: Saving throws, skills, passive perception, senses, languages
- Defensive: Resistances, immunities, vulnerabilities, condition immunities
- Abilities: Traits, actions, reactions, bonus actions, legendary actions
- Metadata: Source name, image URL

## 🤖 Machine Learning Models

### Two-Model Architecture

**Why two models?** CR scales differently at low vs high levels.

#### Low CR Model (CR ≤ 1)
- **Type**: Random Forest Classifier
- **Classes**: 5 discrete values (0, 1/8, 1/4, 1/2, 1)
- **Key features**: HP, AC, attack bonus, basic combat stats
- **Target**: 70%+ exact accuracy, 90%+ within ±1 tier

#### Standard CR Model (CR ≥ 2)
- **Type**: Random Forest Regressor
- **Range**: CR 2-30 (continuous)
- **Key features**: HP, legendary actions, immunities, effective HP
- **Target**: MAE < 2 CR points, 80%+ within ±2 CR

### Feature Engineering

**~60 engineered features** including:
- Parsed numeric: HP avg/dice, AC value, all speed types
- Ability modifiers: Individual + derived (totals, physical/mental splits)
- Combat metrics: HP/AC ratio, effective HP, save/skill counts
- Damage coverage: Resistance/immunity/vulnerability counts
- Senses: Darkvision, blindsight, truesight, passive perception
- Action economy: Trait/action/reaction/legendary counts
- Attack features: Multiattack, highest attack bonus/DC
- Special abilities: Legendary resistance, magic resistance, regeneration, spellcasting
- Categorical: Size (ordinal), Type (one-hot)

## 🔍 Key Insights

The model reveals which features matter most at different CR ranges:

**Low CR (≤1)**:
- HP, AC, and attack bonus are primary
- Small stat differences have big CR impact
- Single extra attack can jump CR by 1/4

**Standard CR (≥2)**:
- Legendary actions become crucial
- Resistances and immunities more important
- Special abilities dominate over raw stats

**High CR (11+)**:
- Legendary actions, lair actions critical
- Immunities and legendary resistance essential
- Action economy > individual stats

## 💻 VS Code & Codespace Setup

### Automatic Configuration

This project includes:
- **`.vscode/settings.json`**: Workspace settings for Python and Jupyter
- **`.vscode/extensions.json`**: Recommended extensions
- **`.devcontainer/devcontainer.json`**: Codespace environment config

### What Happens on Restart

When you reopen this Codespace:
1. ✅ Python environment is preserved
2. ✅ Jupyter extensions are ready
3. ✅ All notebooks open immediately
4. ✅ Dependencies remain installed (unless you rebuild)

### Manual Dependency Refresh

If you need to reinstall dependencies:

```bash
pip install -r requirements.txt
```

Or run the full setup:

```bash
./setup.sh
```

## 📦 Dependencies

Core packages:
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` & `seaborn` - Visualization
- `scikit-learn` - Machine learning
- `jupyter` - Notebook interface

Optional (commented in requirements.txt):
- `xgboost` - Advanced gradient boosting
- `lightgbm` - Fast gradient boosting
- `sentence-transformers` - NLP embeddings

## 📈 Using the Models

### Load Trained Models

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
```

### Predict CR for Custom Monster

```python
# Create feature dictionary
custom_monster = {
    'hp_avg': 45,
    'ac_value': 15,
    'STR_Mod': 3,
    'DEX_Mod': 2,
    # ... (all ~60 features)
}

# Convert to DataFrame
features_df = pd.DataFrame([custom_monster])[feature_columns]

# Route to appropriate model
if features_df['hp_avg'].iloc[0] < 50:
    predicted_cr = low_cr_model.predict(features_df)[0]
else:
    predicted_cr = standard_cr_model.predict(features_df)[0]

print(f"Predicted CR: {predicted_cr}")
```

## 🛠️ Extending the Project

Potential next steps:
1. **Add NLP embeddings** for deeper ability text analysis
2. **Build inverse model**: Input desired CR → get suggested stats
3. **Create web interface** for easy CR prediction
4. **Analyze CR budgeting**: Quantify "cost" of abilities
5. **Model interactions**: Capture synergies (e.g., flight + high AC)
6. **Add 2024 rules**: Compare 2014 vs 2024 CR predictions

## 🐛 Troubleshooting

### Jupyter kernel not found
```bash
pip install ipykernel
python -m ipykernel install --user
```

### Dependencies missing after restart
```bash
./setup.sh
```

### VS Code not recognizing Python
- Check bottom-right corner of VS Code
- Click on Python version and select `/usr/local/bin/python`

### Notebook cells won't run
- Try "Restart Kernel" from the notebook toolbar
- Check that all cells above have completed

## 📄 License

Educational and personal use. D&D 5E content is copyright Wizards of the Coast.

## 🙏 Credits

- **Data Source**: Roll20 Compendium
- **D&D 5E**: Wizards of the Coast
- **Python Libraries**: pandas, scikit-learn, matplotlib, seaborn

---

**Happy Monster Building!** 🎲✨

For detailed documentation:
- Monster Database: See [README_MONSTERS.md](README_MONSTERS.md)
- CR Model Details: See [README_CR_MODEL.md](README_CR_MODEL.md)
