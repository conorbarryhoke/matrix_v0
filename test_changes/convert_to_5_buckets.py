#!/usr/bin/env python3
"""
Script to convert the 3-tier model training cells to 5-bucket model training cells.
"""

import json
import sys

def create_cr1_training_cell():
    """Create training cell for CR < 1 (preserves all-creatures-for-train-and-test logic)"""
    return """print("🤖 TRAINING MODEL FOR CR < 1")
print("=" * 80)

# Phase 2 penalties (lighter for low CR)
PHASE2_PENALTIES_CR1 = {
    'ac_deviation': -3.0,
    'attack_deviation': -4.0,
    'dpr_deviation': -1.5,
    'save_dc_deviation': -7.0,
    'has_flying': -5.0  # Fixed penalty for flying
}

print("📌 CR < 1 Phase 2 Penalties:")
for feat, val in PHASE2_PENALTIES_CR1.items():
    print(f"   {feat:25s} = {val:+.1f} HP per point")

# Calculate HP after Phase 2 (starting from Phase 1.5)
df_cr1['hp_after_phase2'] = df_cr1['hp_after_phase1_5'].copy()
for feature, penalty in PHASE2_PENALTIES_CR1.items():
    df_cr1['hp_after_phase2'] += df_cr1[feature] * penalty

# Calculate scaled features using hp_after_phase2
df_cr1['has_legendary_resistance_scaled'] = df_cr1['has_legendary_resistance'] * df_cr1['hp_after_phase2']
df_cr1['has_magic_resistance_scaled'] = df_cr1['has_magic_resistance'] * df_cr1['hp_after_phase2']
df_cr1['has_regeneration_scaled'] = df_cr1['has_regeneration'] * df_cr1['hp_after_phase2']

# Calculate residual HP (what Phase 3 needs to predict)
df_cr1['residual_hp'] = df_cr1['actual_hp'] - df_cr1['hp_after_phase2']

# Prepare Phase 3 data
X_cr1 = df_cr1[phase3_features].fillna(0)
y_cr1 = df_cr1['residual_hp']  # Target is residual, not actual HP

# For CR < 1: Use all creatures for both training and testing
# (These are simple baseline creatures - we want to validate the model works on them)
X_train_cr1 = X_cr1
X_test_cr1 = X_cr1
y_train_cr1 = y_cr1
y_test_cr1 = y_cr1

print(f"\\n📊 CR < 1 Split Strategy:")
print(f"   All CR < 1 creatures used for both training and testing")
print(f"   Training: {len(X_train_cr1)} creatures")
print(f"   Test: {len(X_test_cr1)} creatures (same as training)")

# Standardize
scaler_cr1 = StandardScaler()
X_train_cr1_scaled = scaler_cr1.fit_transform(X_train_cr1)
X_test_cr1_scaled = scaler_cr1.transform(X_test_cr1)

# Train standard linear regression
model_cr1 = LinearRegression()
model_cr1.fit(X_train_cr1_scaled, y_train_cr1)

coef_cr1 = model_cr1.coef_
intercept_cr1 = model_cr1.intercept_

# Evaluate using ACTUAL HP (not residual)
df_train = df_cr1.loc[X_train_cr1.index]
df_test = df_cr1.loc[X_test_cr1.index]

y_pred_residual_train = model_cr1.predict(X_train_cr1_scaled)
y_pred_residual_test = model_cr1.predict(X_test_cr1_scaled)

y_pred_train_cr1 = df_train['hp_after_phase2'].values + y_pred_residual_train
y_pred_test_cr1 = df_test['hp_after_phase2'].values + y_pred_residual_test

y_actual_train = df_train['actual_hp'].values
y_actual_test = df_test['actual_hp'].values

train_r2_cr1 = 1 - np.sum((y_actual_train - y_pred_train_cr1)**2) / np.sum((y_actual_train - y_actual_train.mean())**2)
test_r2_cr1 = 1 - np.sum((y_actual_test - y_pred_test_cr1)**2) / np.sum((y_actual_test - y_actual_test.mean())**2)
mae_cr1 = np.mean(np.abs(y_actual_test - y_pred_test_cr1))

print(f"\\n📊 CR < 1 Model Performance:")
print(f"   Train R²: {train_r2_cr1:.4f}")
print(f"   Test R²:  {test_r2_cr1:.4f} (same as train - all creatures used)")
print(f"   Test MAE: {mae_cr1:.2f} HP")"""

def create_cr_bucket_training_cell(bucket_num, cr_range_label, penalties):
    """Create training cell for CR buckets 2-5 (with manual train/test split)"""
    return f"""print("🤖 TRAINING MODEL FOR CR {cr_range_label}")
print("=" * 80)

# Phase 2 penalties
PHASE2_PENALTIES_CR{bucket_num} = {{
    'ac_deviation': {penalties['ac']},
    'attack_deviation': {penalties['attack']},
    'dpr_deviation': {penalties['dpr']},
    'save_dc_deviation': {penalties['save_dc']},
    'has_flying': {penalties['flying']}  # Fixed penalty for flying
}}

print("📌 CR {cr_range_label} Phase 2 Penalties:")
for feat, val in PHASE2_PENALTIES_CR{bucket_num}.items():
    print(f"   {{feat:25s}} = {{val:+.1f}} HP per point")

# Calculate HP after Phase 2 (starting from Phase 1.5)
df_cr{bucket_num}['hp_after_phase2'] = df_cr{bucket_num}['hp_after_phase1_5'].copy()
for feature, penalty in PHASE2_PENALTIES_CR{bucket_num}.items():
    df_cr{bucket_num}['hp_after_phase2'] += df_cr{bucket_num}[feature] * penalty

# Calculate scaled features using hp_after_phase2
df_cr{bucket_num}['has_legendary_resistance_scaled'] = df_cr{bucket_num}['has_legendary_resistance'] * df_cr{bucket_num}['hp_after_phase2']
df_cr{bucket_num}['has_magic_resistance_scaled'] = df_cr{bucket_num}['has_magic_resistance'] * df_cr{bucket_num}['hp_after_phase2']
df_cr{bucket_num}['has_regeneration_scaled'] = df_cr{bucket_num}['has_regeneration'] * df_cr{bucket_num}['hp_after_phase2']

# Calculate residual HP (what Phase 3 needs to predict)
df_cr{bucket_num}['residual_hp'] = df_cr{bucket_num}['actual_hp'] - df_cr{bucket_num}['hp_after_phase2']

# Prepare Phase 3 data
X_cr{bucket_num} = df_cr{bucket_num}[phase3_features].fillna(0)
y_cr{bucket_num} = df_cr{bucket_num}['residual_hp']

# Manual train/test split (PRESERVE EXISTING LOGIC)
train_mask = pd.Series(False, index=df_cr{bucket_num}.index)
test_mask = pd.Series(False, index=df_cr{bucket_num}.index)

# Add TRAIN_FAMILIES to training
for family in TRAIN_FAMILIES:
    family_mask = df_cr{bucket_num}['family'] == family
    train_mask |= family_mask

# Add manual TRAIN_CREATURES to training
for creature_name in TRAIN_CREATURES:
    creature_mask = df_cr{bucket_num}['Name'] == creature_name
    if creature_mask.any():
        train_mask |= creature_mask

# Add manual TEST_CREATURES to test
for creature_name in TEST_CREATURES:
    creature_mask = df_cr{bucket_num}['Name'] == creature_name
    if creature_mask.any():
        test_mask |= creature_mask

# Remaining creatures default to training
remaining_mask = ~(train_mask | test_mask)
train_mask |= remaining_mask

X_train_cr{bucket_num} = X_cr{bucket_num}[train_mask]
X_test_cr{bucket_num} = X_cr{bucket_num}[test_mask]
y_train_cr{bucket_num} = y_cr{bucket_num}[train_mask]
y_test_cr{bucket_num} = y_cr{bucket_num}[test_mask]

print(f"\\n📊 Manual Split:")
print(f"   Training: {{len(X_train_cr{bucket_num})}} creatures ({{len(X_train_cr{bucket_num})/len(X_cr{bucket_num})*100:.1f}}%)")
print(f"   Test: {{len(X_test_cr{bucket_num})}} creatures ({{len(X_test_cr{bucket_num})/len(X_cr{bucket_num})*100:.1f}}%)")

# Standardize
scaler_cr{bucket_num} = StandardScaler()
X_train_cr{bucket_num}_scaled = scaler_cr{bucket_num}.fit_transform(X_train_cr{bucket_num})
X_test_cr{bucket_num}_scaled = scaler_cr{bucket_num}.transform(X_test_cr{bucket_num})

# Train standard linear regression
model_cr{bucket_num} = LinearRegression()
model_cr{bucket_num}.fit(X_train_cr{bucket_num}_scaled, y_train_cr{bucket_num})

coef_cr{bucket_num} = model_cr{bucket_num}.coef_
intercept_cr{bucket_num} = model_cr{bucket_num}.intercept_

# Evaluate using ACTUAL HP (not residual)
df_train = df_cr{bucket_num}.loc[X_train_cr{bucket_num}.index]
df_test = df_cr{bucket_num}.loc[X_test_cr{bucket_num}.index]

y_pred_residual_train = model_cr{bucket_num}.predict(X_train_cr{bucket_num}_scaled)
y_pred_residual_test = model_cr{bucket_num}.predict(X_test_cr{bucket_num}_scaled)

y_pred_train_cr{bucket_num} = df_train['hp_after_phase2'].values + y_pred_residual_train
y_pred_test_cr{bucket_num} = df_test['hp_after_phase2'].values + y_pred_residual_test

y_actual_train = df_train['actual_hp'].values
y_actual_test = df_test['actual_hp'].values

train_r2_cr{bucket_num} = 1 - np.sum((y_actual_train - y_pred_train_cr{bucket_num})**2) / np.sum((y_actual_train - y_actual_train.mean())**2)
test_r2_cr{bucket_num} = 1 - np.sum((y_actual_test - y_pred_test_cr{bucket_num})**2) / np.sum((y_actual_test - y_actual_test.mean())**2)
mae_cr{bucket_num} = np.mean(np.abs(y_actual_test - y_pred_test_cr{bucket_num}))

print(f"\\n📊 CR {cr_range_label} Model Performance:")
print(f"   Train R²: {{train_r2_cr{bucket_num}:.4f}}")
print(f"   Test R²:  {{test_r2_cr{bucket_num}:.4f}}")
print(f"   Test MAE: {{mae_cr{bucket_num}:.2f}} HP")"""

def main():
    # Load notebook
    with open('/workspaces/matrix_v0/notebooks/three_tier_hp_model_v2.ipynb', 'r') as f:
        nb = json.load(f)

    # Define penalty values for each bucket (matching old values as baseline)
    penalties = {
        1: {'ac': -3.0, 'attack': -4.0, 'dpr': -1.5, 'save_dc': -7.0, 'flying': -5.0},  # CR < 1
        2: {'ac': -5.0, 'attack': -6.0, 'dpr': -2.0, 'save_dc': -10.0, 'flying': -8.0},  # CR 1-4
        3: {'ac': -7.0, 'attack': -8.0, 'dpr': -2.5, 'save_dc': -12.0, 'flying': -10.0},  # CR 5-10
        4: {'ac': -9.0, 'attack': -10.0, 'dpr': -3.0, 'save_dc': -15.0, 'flying': -12.0},  # CR 11-16
        5: {'ac': -12.0, 'attack': -13.0, 'dpr': -4.0, 'save_dc': -18.0, 'flying': -15.0},  # CR > 16
    }

    # Create 5 new training cells
    cr1_cell = create_cr1_training_cell()
    cr2_cell = create_cr_bucket_training_cell(2, "1-4", penalties[2])
    cr3_cell = create_cr_bucket_training_cell(3, "5-10", penalties[3])
    cr4_cell = create_cr_bucket_training_cell(4, "11-16", penalties[4])
    cr5_cell = create_cr_bucket_training_cell(5, "> 16", penalties[5])

    # Find and remove the old 3 training cells (cells 20, 22, 24)
    # Delete in reverse order to preserve indices
    del nb['cells'][24]  # HIGH-CR
    del nb['cells'][22]  # MID-CR
    del nb['cells'][20]  # LOW-CR

    # Insert 5 new training cells at position 20
    new_cells = []
    for cell_content in [cr1_cell, cr2_cell, cr3_cell, cr4_cell, cr5_cell]:
        new_cell = {
            'cell_type': 'code',
            'execution_count': None,
            'metadata': {},
            'outputs': [],
            'source': [line + '\n' for line in cell_content.split('\n')[:-1]] + [cell_content.split('\n')[-1]]
        }
        new_cells.append(new_cell)

    # Insert all new cells at position 20
    for i, cell in enumerate(new_cells):
        nb['cells'].insert(20 + i, cell)

    # Save
    with open('/workspaces/matrix_v0/notebooks/three_tier_hp_model_v2.ipynb', 'w') as f:
        json.dump(nb, f, indent=1)

    print("✅ Phase 2 Complete: Created 5 model training cells")
    print("   - Cell 20: CR < 1 (all creatures for train & test)")
    print("   - Cell 21: CR 1-4 (manual train/test split)")
    print("   - Cell 22: CR 5-10 (manual train/test split)")
    print("   - Cell 23: CR 11-16 (manual train/test split)")
    print("   - Cell 24: CR > 16 (manual train/test split)")
    print("\nNext: Phase 3 - Update model saving to create 5 pickle files")

if __name__ == '__main__':
    main()
