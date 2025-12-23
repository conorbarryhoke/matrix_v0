# 🚀 Quick Start Guide

## First Time Opening This Codespace

```bash
# 1. Run setup script
./setup.sh

# 2. Open the notebook
# Click on: cr_prediction_model.ipynb

# 3. Select Python kernel when prompted

# 4. Click "Run All" at the top
```

## Every Time You Restart This Codespace

**Good news**: Everything is already configured!

Just open `cr_prediction_model.ipynb` and start working. Your environment is preserved.

## Common Commands

```bash
# Reinstall dependencies (if needed)
pip install -r requirements.txt

# Run setup script
./setup.sh

# Parse monsters data again
python3 parse_monsters.py

# Launch Jupyter in browser
jupyter notebook
```

## File Map

| File | Purpose |
|------|---------|
| `cr_prediction_model.ipynb` | **Main notebook** - Run this! |
| `dnd5e_monsters_2014.csv` | Monster database (324 monsters) |
| `requirements.txt` | Python dependencies |
| `setup.sh` | Setup script |
| `README.md` | Full documentation |

## What the Notebook Does

1. ✅ Loads 324 D&D monsters
2. ✅ Engineers 60+ features
3. ✅ Trains 2 models (low CR + standard CR)
4. ✅ Shows feature importance
5. ✅ Predicts CR for custom monsters

## Expected Runtime

- Full notebook: ~1-2 minutes
- Results: Model performance, feature importance, visualizations

## Troubleshooting

**Kernel not found?**
```bash
pip install ipykernel
```

**Dependencies missing?**
```bash
./setup.sh
```

**Notebook won't run?**
- Check you selected Python kernel (bottom right)
- Try "Restart Kernel" from toolbar

## Output Files

After running the notebook, you'll get:
- `low_cr_model.pkl` - Trained low CR classifier
- `standard_cr_model.pkl` - Trained standard CR regressor
- `feature_columns.pkl` - List of features

These can be loaded to predict CR for custom monsters!

---

**That's it!** Open the notebook and run it. Everything else is automatic. 🎲
