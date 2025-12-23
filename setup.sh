#!/bin/bash
# Setup script for D&D Monster CR Prediction environment

echo "🎲 Setting up D&D Monster CR Prediction Environment..."
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements.txt --quiet

# Check if data files exist
echo ""
echo "📊 Checking data files..."
if [ -f "dnd5e_monsters_2014.csv" ]; then
    echo "✅ Monster database found ($(wc -l < dnd5e_monsters_2014.csv) entries)"
else
    echo "⚠️  Monster database not found - run parse_monsters.py if needed"
fi

if [ -f "monsters_data.json" ]; then
    echo "✅ Raw JSON data found"
else
    echo "⚠️  Raw JSON data not found"
fi

# Check notebook
if [ -f "cr_prediction_model.ipynb" ]; then
    echo "✅ CR prediction notebook ready"
else
    echo "⚠️  Notebook not found"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Open cr_prediction_model.ipynb in VS Code"
echo "   2. Select Python kernel when prompted"
echo "   3. Run all cells to train the models"
echo ""
echo "🚀 Happy monster building!"
