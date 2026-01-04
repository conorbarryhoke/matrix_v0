# Quick Start Guide

## 🚀 Get Your Monster Builder Live in 5 Minutes

### Option 1: GitHub Pages (Free, Permanent)

1. **Create GitHub Account** (if you don't have one): https://github.com/signup

2. **Create New Repository**:
   - Go to: https://github.com/new
   - Repository name: `dnd-monster-builder`
   - Make it **Public**
   - Click **Create repository**

3. **Upload Files**:
   - Click "uploading an existing file"
   - Drag ALL 6 files from `monster-builder-app/` folder:
     - `index.html`
     - `styles.css`
     - `app.js`
     - `model_data.json`
     - `README.md`
     - `DEPLOYMENT.md`
   - Click **Commit changes**

4. **Enable GitHub Pages**:
   - Click **Settings** (top right)
   - Click **Pages** (left sidebar)
   - Under "Source":
     - Branch: **main**
     - Folder: **/ (root)**
   - Click **Save**

5. **Visit Your Site** (after 1-2 minutes):
   ```
   https://YOUR-USERNAME.github.io/dnd-monster-builder/
   ```

**Done!** 🎉

---

### Option 2: Netlify Drop (Fastest)

1. Go to: https://app.netlify.com/drop

2. Drag the entire `monster-builder-app` folder onto the page

3. Your site is live instantly at a URL like:
   ```
   https://epic-monster-builder-abc123.netlify.app
   ```

**Done!** 🎉

---

### Option 3: Local Testing (No Internet Required)

**Using Python**:
```bash
cd monster-builder-app
python3 -m http.server 8000
```

Visit: http://localhost:8000

**Using VS Code**:
1. Open `monster-builder-app` folder in VS Code
2. Install "Live Server" extension
3. Right-click `index.html` → "Open with Live Server"

---

## 🎮 How to Use

### Creating Your First Monster

1. **Set Challenge Rating**: Enter CR (e.g., 3)
2. **Set Armor Class**: Enter AC (e.g., 14)
3. **Set Attack Bonus**: Enter +X to hit (e.g., 5)
4. **Click a Size**: Choose from Tiny to Gargantuan
5. **Check Special Abilities**: Multiattack, Legendary Actions, etc.

The HP updates automatically!

### Making a Spellcaster

1. Check **Spellcasting** box
2. Set **Spellcaster Level** (1-20)
3. Choose **Highest Spell Level** (Cantrips to 9th)

The model accounts for spellcasting in HP!

### Understanding the Results

- **Predicted HP**: What the AI suggests
- **HP Dice**: Hit dice notation (e.g., 8d8+16)
- **Effective HP**: With resistances factored in
- **Suggested DPR**: Damage per round range from DMG
- **DMG Baseline HP**: Official guidelines
- **HP vs Baseline**: How far off from DMG

### Copying the Stat Block

1. Review the generated stat block
2. Click **📋 Copy Stat Block**
3. Paste into your notes, VTT, or document

---

## 📊 Example: Creating a CR 3 Ambusher

```
Name: Shadow Stalker
CR: 3
AC: 15
Attack: +6
Save DC: 13
Size: Medium
Speed: 40 ft

Special Abilities:
✓ Multiattack
✓ Darkvision

Defensive:
Resistances: 0
Immunities: 0
```

**Result**: ~53 HP (predicted by model)

Now add some resistances:
```
Resistances: 2
```

**Result**: HP might increase to ~60-65 (model accounts for survivability)

---

## 🎲 Try the Random Monster Generator

Click **🎲 Random Monster** to get instant inspiration!

The generator creates:
- Random CR (0.125 to 10)
- Appropriate AC for that CR
- Random size
- Random special abilities
- Cool random name

Great for:
- Quick encounters
- Testing the tool
- Inspiration for custom creatures

---

## 📋 Keyboard Shortcuts

- **Tab**: Move between fields
- **Enter**: (in number fields) Trigger recalculation
- **Ctrl+C**: (after clicking Copy) Stat block in clipboard

---

## 🔧 Troubleshooting

### "Error loading model data"
- Make sure all files are in the same folder
- Use a web server (not opening file:// directly)
- Check browser console (F12) for details

### HP seems wrong
- Check the DMG baseline comparison
- Model trained on 2014 Basic Rules monsters
- Custom feature combinations may vary

### Copy button doesn't work
- Use HTTPS or localhost (clipboard API requirement)
- Or manually select and copy the stat block text

---

## 🎯 Pro Tips

1. **Start with DMG Guidelines**: Use the suggested DPR range to balance offense/defense

2. **Resistance = Survivability**: Each resistance adds ~15-25% effective HP

3. **Spellcasters Get Less HP**: Model reduces HP for spellcasters (they have offensive power)

4. **Legendary Actions = More HP**: Model increases HP to compensate for action economy

5. **Compare to Baseline**: Use the "HP vs Baseline" to see if you're making a glass cannon or tank

6. **Mobile Friendly**: Works great on tablets for at-the-table creation

---

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed features
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for hosting options
- Customize colors in `styles.css`
- Add your own creature types
- Share your creations!

---

## 🆘 Need Help?

- **Check Browser Console**: Press F12, look for errors in red
- **Verify Files**: Make sure all 4 core files are present
- **Test Locally First**: Use Python server to test before deploying
- **GitHub Issues**: Report bugs on the repository

---

**Happy Monster Building!** 🐉

Your monsters are one click away from coming alive!
