#!/usr/bin/env python3
"""
Complete conversion script: Updates all remaining cells from 3-tier to 5-bucket system.
Handles: analysis, predictions, exports, visualizations, and feature contributions.
"""

import json
import re

def update_cell_source(source):
    """Update source code from 3-tier to 5-bucket naming"""

    # Update dataframe references
    replacements = [
        # Dataframes
        (r'\bdf_low_cr\b', 'df_cr1'),
        (r'\bdf_mid_cr\b', 'df_cr2'),
        (r'\bdf_high_cr\b', 'df_cr3'),

        # Models
        (r'\bmodel_low\b', 'model_cr1'),
        (r'\bmodel_mid\b', 'model_cr2'),
        (r'\bmodel_high\b', 'model_cr3'),

        # Scalers
        (r'\bscaler_low\b', 'scaler_cr1'),
        (r'\bscaler_mid\b', 'scaler_cr2'),
        (r'\bscaler_high\b', 'scaler_cr3'),

        # Coefficients
        (r'\bcoef_low\b', 'coef_cr1'),
        (r'\bcoef_mid\b', 'coef_cr2'),
        (r'\bcoef_high\b', 'coef_cr3'),
        (r'\bintercept_low\b', 'intercept_cr1'),
        (r'\bintercept_mid\b', 'intercept_cr2'),
        (r'\bintercept_high\b', 'intercept_cr3'),

        # Predictions
        (r'\by_pred_low\b', 'y_pred_cr1'),
        (r'\by_pred_mid\b', 'y_pred_cr2'),
        (r'\by_pred_high\b', 'y_pred_cr3'),
        (r'\by_low\b', 'y_cr1'),
        (r'\by_mid\b', 'y_cr2'),
        (r'\by_high\b', 'y_cr3'),

        # Feature sets
        (r'\bX_low\b', 'X_cr1'),
        (r'\bX_mid\b', 'X_cr2'),
        (r'\bX_high\b', 'X_cr3'),
        (r'\bX_train_low\b', 'X_train_cr1'),
        (r'\bX_train_mid\b', 'X_train_cr2'),
        (r'\bX_train_high\b', 'X_train_cr3'),
        (r'\bX_test_low\b', 'X_test_cr1'),
        (r'\bX_test_mid\b', 'X_test_cr2'),
        (r'\bX_test_high\b', 'X_test_cr3'),

        # R2 and MAE
        (r'\btest_r2_low\b', 'test_r2_cr1'),
        (r'\btest_r2_mid\b', 'test_r2_cr2'),
        (r'\btest_r2_high\b', 'test_r2_cr3'),
        (r'\bmae_low\b', 'mae_cr1'),
        (r'\bmae_mid\b', 'mae_cr2'),
        (r'\bmae_high\b', 'mae_cr3'),

        # Analysis
        (r'\banalysis_low\b', 'analysis_cr1'),
        (r'\banalysis_mid\b', 'analysis_cr2'),
        (r'\banalysis_high\b', 'analysis_cr3'),

        # Is train
        (r'\bis_train_low\b', 'is_train_cr1'),
        (r'\bis_train_mid\b', 'is_train_cr2'),
        (r'\bis_train_high\b', 'is_train_cr3'),

        # Penalties
        (r'\bPHASE2_PENALTIES_LOW\b', 'PHASE2_PENALTIES_CR1'),
        (r'\bPHASE2_PENALTIES_MID\b', 'PHASE2_PENALTIES_CR2'),
        (r'\bPHASE2_PENALTIES_HIGH\b', 'PHASE2_PENALTIES_CR3'),

        # Labels in strings
        (r'"Low-CR \(≤ 1\)"', '"CR < 1"'),
        (r'"Low-CR \(CR ≤ 1\)"', '"CR < 1"'),
        (r'"Mid-CR \(1 < CR ≤ 12\)"', '"CR 1-4"'),  # This will need manual fixing for split
        (r'"High-CR \(CR > 12\)"', '"CR > 16"'),
        (r"'Low-CR \(≤ 1\)'", "'CR < 1'"),
        (r"'Low-CR \(CR ≤ 1\)'", "'CR < 1'"),
        (r"'Mid-CR \(1 < CR ≤ 12\)'", "'CR 1-4'"),
        (r"'High-CR \(CR > 12\)'", "'CR > 16'"),

        # CR range checks
        (r'cr <= 1\.0', 'cr < 1.0'),
        (r'cr <= 12\.0', 'cr <= 10.0'),  # Will need manual adjustment
        (r'cr > 12\.0', 'cr > 16.0'),
    ]

    for pattern, replacement in replacements:
        source = re.sub(pattern, replacement, source)

    return source

def main():
    print("🔄 Starting comprehensive 3-tier to 5-bucket conversion...")
    print("=" * 80)

    # Load notebook
    with open('/workspaces/matrix_v0/notebooks/three_tier_hp_model_v2.ipynb', 'r') as f:
        nb = json.load(f)

    # Track changes
    cells_modified = 0

    # Update cells 26 onwards (after training and saving cells)
    for i in range(26, len(nb['cells'])):
        cell = nb['cells'][i]
        if cell['cell_type'] != 'code':
            continue

        original_source = ''.join(cell['source'])

        # Check if this cell needs updating
        needs_update = any(old in original_source for old in [
            'df_low_cr', 'df_mid_cr', 'df_high_cr',
            'model_low', 'model_mid', 'model_high',
            'scaler_low', 'scaler_mid', 'scaler_high',
            'intercept_low', 'intercept_mid', 'intercept_high',
            'PHASE2_PENALTIES_LOW', 'PHASE2_PENALTIES_MID', 'PHASE2_PENALTIES_HIGH'
        ])

        if needs_update:
            updated_source = update_cell_source(original_source)

            # Convert back to cell format
            nb['cells'][i]['source'] = [line + '\n' for line in updated_source.split('\n')[:-1]] + [updated_source.split('\n')[-1]]

            cells_modified += 1
            print(f"  ✓ Updated cell {i}")

    # Save
    with open('/workspaces/matrix_v0/notebooks/three_tier_hp_model_v2.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)

    print("=" * 80)
    print(f"✅ Conversion complete: {cells_modified} cells updated")
    print("\n⚠️  MANUAL REVIEW NEEDED:")
    print("   - Cells with model selection logic (cr <= 1.0, cr <= 12.0)")
    print("   - Export cells that reference 'low_cr', 'mid_cr', 'high_cr' in keys")
    print("   - Visualization cells that create 3 subplots (need 5 or adjust)")
    print("   - Analysis concat() calls that combine 3 dataframes (need 5)")
    print("\n📝 Next steps:")
    print("   1. Search for 'cr <= 10.0' and update to appropriate bucket boundaries")
    print("   2. Search for 'pd.concat([' and add cr4, cr5 dataframes")
    print("   3. Search for 'low_cr', 'mid_cr', 'high_cr' in dictionary keys")
    print("   4. Test the notebook!")

if __name__ == '__main__':
    main()
