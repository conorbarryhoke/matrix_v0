# Workspace Configuration

This directory contains user preferences and workspace settings.

## Files

- `user_preferences.json` - User-specific preferences including notebook execution settings

## Notebook Execution Preference

**Setting**: User executes notebooks manually (auto_execute: false)

**When to remind**: After making changes to notebooks, display the reminder message from user_preferences.json

**Command to run**:
```bash
cd /workspaces/matrix_v0 && jupyter nbconvert --to notebook --execute notebooks/three_tier_hp_model.ipynb --output three_tier_hp_model_executed.ipynb --ExecutePreprocessor.timeout=600
```
