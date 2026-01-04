# D&D 5E Monster Builder

AI-powered monster creation tool using machine learning to predict Hit Points based on creature attributes.

## 🎯 Features

- **AI-Powered HP Prediction**: Uses a trained Linear Regression model (R² = 0.86) based on 324 official D&D 5E monsters
- **Intuitive Interface**: Simple form-based UI for rapid monster creation
- **Core Attributes**: CR, AC, Attack Bonus, Save DC with automatic DPR suggestions
- **Special Abilities**: Spellcasting support with spell level tracking
- **Defensive Features**: Resistance/immunity counts that affect HP predictions
- **Stat Block Generation**: Auto-generates formatted D&D stat blocks
- **Random Monster Generator**: Create random creatures for inspiration
- **DMG Integration**: Shows DMG baseline comparisons and effective HP calculations

## 🚀 Quick Start

### Option 1: Local Development

1. Clone or download this folder
2. Open `index.html` in a modern web browser
3. Start creating monsters!

**Note**: Due to CORS restrictions, you may need to run a local server:

```bash
# Using Python 3
python3 -m http.server 8000

# Using Node.js (if you have http-server installed)
npx http-server

# Using PHP
php -S localhost:8000
```

Then visit `http://localhost:8000`

### Option 2: GitHub Pages Deployment

#### Step 1: Prepare Your Repository

1. Create a new GitHub repository (or use an existing one)
2. Upload all files from the `monster-builder-app` folder to your repository:
   - `index.html`
   - `styles.css`
   - `app.js`
   - `model_data.json`
   - `README.md`

#### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (in the left sidebar)
3. Under **Source**, select:
   - Branch: `main` (or `master`)
   - Folder: `/` (root) or `/docs` if you put files there
4. Click **Save**

#### Step 3: Access Your Site

After a few minutes, your site will be live at:
```
https://[your-username].github.io/[repository-name]/
```

Example: `https://johnsmith.github.io/monster-builder/`

### Option 3: Other Static Hosting Services

This app can be deployed to any static site hosting service:

- **Netlify**: Drag and drop the folder to [netlify.com/drop](https://app.netlify.com/drop)
- **Vercel**: Install Vercel CLI and run `vercel` in the folder
- **Cloudflare Pages**: Connect your Git repository
- **GitHub Codespaces**: Use the Live Server extension

## 📁 File Structure

```
monster-builder-app/
├── index.html          # Main HTML structure
├── styles.css          # All styling
├── app.js             # Application logic and ML model
├── model_data.json    # Trained model coefficients
└── README.md          # This file
```

## 🎮 How to Use

### Basic Monster Creation

1. **Set Core Attributes**:
   - Challenge Rating (0-30)
   - Armor Class (1-25)
   - Attack Bonus (0-20)
   - Save DC (8-25)

2. **Choose Size**: Tiny, Small, Medium, Large, Huge, or Gargantuan

3. **Add Special Abilities**:
   - Multiattack
   - Legendary Actions
   - Spellcasting (with spell level support)
   - Magic Resistance
   - Regeneration

4. **Set Defensive Features**:
   - Damage resistances (increases effective HP)
   - Damage immunities
   - Special senses

5. **View Results**:
   - Predicted HP with hit dice notation
   - Effective HP calculation
   - DMG baseline comparison
   - Suggested DPR range
   - Full stat block

### Spellcaster Creation

1. Check the **Spellcasting** checkbox
2. Set the **Spellcaster Level** (1-20)
3. Select the **Highest Spell Level** (Cantrips to 9th)
4. The model automatically adjusts HP based on spellcasting capability

### Using the Buttons

- **🔄 Recalculate**: Manually refresh HP (auto-calculates on input)
- **📋 Copy Stat Block**: Copy formatted stat block to clipboard
- **🎲 Random Monster**: Generate a random creature for inspiration

## 🧠 How It Works

### The Model

The HP prediction uses a **Linear Regression model** trained on 324 official D&D 5E monsters from the 2014 Basic Rules. The model:

- **R² Score**: 0.86 (explains 86% of HP variance)
- **MAE**: ~18 HP average error
- **Features**: 74 interpretable features including:
  - CR (strongest predictor)
  - Size, AC, Speed
  - Special abilities (legendary, spellcasting, etc.)
  - Resistance count (survivability proxy)
  - Senses and action economy

### Key Design Decisions

1. **Resistance Count as Survivability**: Instead of calculating effective HP directly, the model uses resistance count as an independent metric
2. **No Ability Scores**: Model excludes STR, DEX, CON, etc. for interpretability
3. **CR Inclusion**: CR is included as a predictor since designers typically know the target CR
4. **Spellcaster Support**: Spell level directly impacts predicted HP

### Prediction Formula

```javascript
HP = intercept + Σ(scaled_feature × coefficient)
```

Where each feature is standardized (z-score normalized) before applying its coefficient.

## 📊 DMG Integration

The app includes the official DMG CR table for reference:

- **Baseline HP Comparison**: Shows if your creature is above/below DMG guidelines
- **Suggested DPR Range**: Provides damage per round recommendations
- **Effective HP**: Accounts for resistances and immunities

## 🎨 Customization

### Modify Appearance

Edit `styles.css` to change:
- Color scheme (update gradient values)
- Font sizes and spacing
- Layout (grid columns, padding)

### Adjust Model Behavior

Edit `app.js` to:
- Change CON modifier assumptions (line ~100)
- Modify effective HP calculation (line ~247)
- Adjust auto-generated ability scores (lines ~330-340)

### Update Model Data

To use a different trained model:

1. Export your model to JSON format matching:
```json
{
  "intercept": 83.96,
  "coefficients": { "feature_name": coefficient_value },
  "scaler_mean": { "feature_name": mean_value },
  "scaler_scale": { "feature_name": scale_value },
  "feature_columns": ["feature1", "feature2", ...]
}
```

2. Replace `model_data.json`

## 🐛 Troubleshooting

### Model data not loading

- **Issue**: "Error loading model data" message
- **Solution**: Ensure `model_data.json` is in the same folder as `index.html`
- **Check**: Open browser console (F12) for detailed error messages

### HP predictions seem off

- **Issue**: HP values don't match expectations
- **Explanation**: Model is trained on 2014 Basic Rules monsters. Custom features may predict differently
- **Solution**: Use DMG baseline comparison as a reality check

### Stat block not copying

- **Issue**: Copy button doesn't work
- **Solution**: Ensure you're using HTTPS or localhost (clipboard API requirement)
- **Workaround**: Manually select and copy the stat block text

### Buttons not working

- **Issue**: Nothing happens when clicking buttons
- **Solution**: Check browser console for JavaScript errors
- **Common cause**: Missing `model_data.json` file

## 📝 License

This tool is based on D&D 5E rules, which are copyrighted by Wizards of the Coast. This is a fan-made tool for educational and personal use.

The machine learning model and code are MIT licensed.

## 🙏 Credits

- **Model Training**: Based on 324 monsters from D&D 5E 2014 Basic Rules
- **Data Source**: Roll20 Compendium
- **ML Framework**: Scikit-learn (Python) → JavaScript port
- **Design**: Inspired by D&D Beyond and DNDMasterVault

## 🔗 Links

- [D&D Beyond](https://www.dndbeyond.com/) - Official digital tools
- [Dungeon Master's Guide](https://dnd.wizards.com/) - Official monster design rules
- [GitHub Repository](https://github.com) - Source code and model

## 📮 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Submit a pull request
- Contact the maintainer

---

**Happy Monster Building!** 🐉✨
