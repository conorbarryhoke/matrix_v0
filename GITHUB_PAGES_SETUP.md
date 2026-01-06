# GitHub Pages Deployment Guide

This repository contains multiple web applications that can be deployed to GitHub Pages.

## Available Sites

### 1. Monster Builder App (Primary)
**Location**: `monster-builder-app/`
**Description**: D&D 5e Monster HP Prediction Tool with 88 features including conditions
**URL**: `https://conorbarryhoke.github.io/matrix_v0/monster-builder-app/`

### 2. Monsters List
**Location**: `monsters_list.html`
**Description**: D&D 5e Monsters compendium page
**URL**: `https://conorbarryhoke.github.io/matrix_v0/monsters_list.html`

---

## Quick Deployment Instructions

### Option 1: Deploy from Current Repository (Recommended)

1. **Push your changes to GitHub**:
   ```bash
   git add .
   git commit -m "Add monster builder app and monsters list"
   git push origin main
   ```

2. **Enable GitHub Pages**:
   - Go to: https://github.com/conorbarryhoke/matrix_v0/settings/pages
   - Under "Source", select branch: `main`
   - Under "Folder", select: `/ (root)`
   - Click "Save"

3. **Wait 2-3 minutes**, then visit:
   - Monster Builder: `https://conorbarryhoke.github.io/matrix_v0/monster-builder-app/`
   - Monsters List: `https://conorbarryhoke.github.io/matrix_v0/monsters_list.html`

### Option 2: Deploy as Separate Repository (Standalone)

If you want the Monster Builder at the root URL:

1. **Create new repository**:
   ```bash
   # Create new repo on GitHub named "monster-builder"
   cd /workspaces/matrix_v0/monster-builder-app
   git init
   git add .
   git commit -m "Initial commit: D&D Monster Builder"
   git remote add origin https://github.com/conorbarryhoke/monster-builder.git
   git push -u origin main
   ```

2. **Enable GitHub Pages** for the new repo (steps same as above)

3. **Access at**: `https://conorbarryhoke.github.io/monster-builder/`

---

## Creating an Index Page (Optional)

You might want to create an index page at the root to link to both apps:

**File**: `index.html` (in root directory)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D&D Tools by Conor Barry Hoke</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .card {
            background: white;
            color: #333;
            padding: 30px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { text-align: center; }
        a {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
        }
        a:hover { background: #764ba2; }
    </style>
</head>
<body>
    <h1>🎲 D&D 5e Tools</h1>

    <div class="card">
        <h2>Monster HP Builder</h2>
        <p>AI-powered monster HP prediction tool with 88 features including CR, AC, damage output, special abilities, and condition infliction.</p>
        <a href="monster-builder-app/">Launch Monster Builder →</a>
    </div>

    <div class="card">
        <h2>Monsters List</h2>
        <p>Comprehensive D&D 5e monsters compendium from Roll20.</p>
        <a href="monsters_list.html">View Monsters List →</a>
    </div>
</body>
</html>
```

---

## Troubleshooting

### Site not loading?
- Check GitHub Actions tab for build status
- Ensure all files are committed and pushed
- Wait 2-3 minutes after enabling Pages

### 404 errors on model_data_with_conditions.json?
- Make sure the file is in the `monster-builder-app/` folder
- Check the fetch path in `app.js` line 49

### CORS errors?
- GitHub Pages serves files with correct CORS headers
- If testing locally, use a local server: `python -m http.server 8000`

---

## Current Repository Structure

```
matrix_v0/
├── monster-builder-app/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── model_data_with_conditions.json
│   ├── model_data.json (backup)
│   └── README.md
├── monsters_list.html
├── dnd5e_monsters_2014.csv
└── (Python scripts and models)
```

After deployment, your sites will be available at:
- **Monster Builder**: https://conorbarryhoke.github.io/matrix_v0/monster-builder-app/
- **Monsters List**: https://conorbarryhoke.github.io/matrix_v0/monsters_list.html
