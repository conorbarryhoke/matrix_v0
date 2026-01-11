#!/usr/bin/env python3
"""
Verification script for new baseline features.
Tests that size_ordinal, speed_ground, and max_speed baselines are correctly implemented.
"""

import json
import pandas as pd

print("=" * 80)
print("VERIFYING NEW BASELINE FEATURES")
print("=" * 80)

# Test 1: Check baseline_lookup_three_tier.json has new keys
print("\n1. Checking baseline_lookup_three_tier.json...")
with open('data/baseline_lookup_three_tier.json', 'r') as f:
    baselines = json.load(f)

required_keys = ['size_ordinal_baseline', 'speed_ground_baseline', 'max_speed_baseline']
for key in required_keys:
    if key in baselines:
        print(f"   ✓ {key} found")
    else:
        print(f"   ✗ {key} MISSING!")

# Test 2: Verify size_ordinal_baseline values
print("\n2. Verifying size_ordinal_baseline values...")
size_baseline = baselines['size_ordinal_baseline']
cr_values = baselines['cr_values']

# Check that values are 2 for CR < 12, 3 for CR >= 12
errors = []
for cr, size in zip(cr_values, size_baseline):
    expected = 2 if cr < 12 else 3
    if size != expected:
        errors.append(f"CR {cr}: expected {expected}, got {size}")

if errors:
    print(f"   ✗ Found {len(errors)} errors:")
    for err in errors[:5]:  # Show first 5 errors
        print(f"      {err}")
else:
    print(f"   ✓ All {len(size_baseline)} values correct")
    print(f"      - CR < 12: {size_baseline[cr_values.index(11.0)]} (expected 2)")
    print(f"      - CR = 12: {size_baseline[cr_values.index(12.0)]} (expected 3)")
    print(f"      - CR = 13: {size_baseline[cr_values.index(13.0)]} (expected 3)")

# Test 3: Verify speed baselines are all 30
print("\n3. Verifying speed baselines...")
speed_ground = baselines['speed_ground_baseline']
max_speed = baselines['max_speed_baseline']

if all(s == 30 for s in speed_ground):
    print(f"   ✓ speed_ground_baseline: all {len(speed_ground)} values are 30")
else:
    print(f"   ✗ speed_ground_baseline has non-30 values!")

if all(s == 30 for s in max_speed):
    print(f"   ✓ max_speed_baseline: all {len(max_speed)} values are 30")
else:
    print(f"   ✗ max_speed_baseline has non-30 values!")

# Test 4: Check engineered_features.csv has the required columns
print("\n4. Checking engineered_features.csv for required columns...")
try:
    df = pd.read_csv('data/engineered_features.csv')
    required_cols = ['size_ordinal', 'speed_ground', 'max_speed']

    for col in required_cols:
        if col in df.columns:
            print(f"   ✓ {col} column exists")
        else:
            print(f"   ✗ {col} column MISSING!")

    # Show sample values
    print("\n   Sample values:")
    sample = df[['Name', 'size_ordinal', 'speed_ground', 'max_speed']].head(5)
    print(sample.to_string(index=False))

except FileNotFoundError:
    print("   ℹ engineered_features.csv not found (will be created on notebook run)")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\nNext step: Run the notebook to apply these changes and retrain the model.")
print("The notebook will:")
print("  1. Create baseline columns in lazy_5e dataframe")
print("  2. Create interpolation functions for new baselines")
print("  3. Add baseline and deviation columns to main df")
print("  4. Train models using the new deviation features")
print("  5. Save updated pickled models")
