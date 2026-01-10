#!/usr/bin/env python3
"""
Execute the updated three-tier HP model notebook.

This script runs the three_tier_hp_model.ipynb notebook with the new:
- Phase 1.5 for resistances/immunities (fixed formula)
- Legendary actions parsing (damage-maximizing)
- Updated feature set (42 features)

The results will be saved back to the notebook with all outputs included.
"""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import sys
from pathlib import Path

def main():
    notebook_path = Path(__file__).parent / 'notebooks' / 'three_tier_hp_model.ipynb'

    print(f"Reading notebook: {notebook_path}")

    # Read notebook
    with open(notebook_path, 'r') as f:
        nb = nbformat.read(f, as_version=4)

    print("Executing notebook (this may take several minutes)...")
    print("This will:")
    print("  - Parse legendary actions for DPR and conditions")
    print("  - Apply Phase 1.5 resistances/immunities penalties")
    print("  - Train three CR-specific models (low, mid, high)")
    print("  - Export models to pickled_models/ and monster-builder-v2/")

    # Execute
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb, {'metadata': {'path': str(notebook_path.parent)}})
    except Exception as e:
        print(f"❌ Error executing notebook: {e}", file=sys.stderr)
        sys.exit(1)

    # Save with outputs
    print(f"Saving results to: {notebook_path}")
    with open(notebook_path, 'w') as f:
        nbformat.write(nb, f)

    print('✅ Three-tier HP model training completed successfully!')
    print(f'   Results saved to: {notebook_path}')
    print('   Models exported to:')
    print('     - pickled_models/hp_model_low_cr.pkl')
    print('     - pickled_models/hp_model_mid_cr.pkl')
    print('     - pickled_models/hp_model_high_cr.pkl')
    print('     - monster-builder-v2/model_data.json')

if __name__ == '__main__':
    main()
