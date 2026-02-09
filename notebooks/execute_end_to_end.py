#!/usr/bin/env python3
"""
Execute the HP prediction model pipeline end-to-end.

This script runs the complete pipeline:
1. Feature Engineering: Raw data → engineered features
2. Model Training: Features → trained models
3. Model Analysis: Models → predictions and exports

Usage:
    python execute_end_to_end.py
    python execute_end_to_end.py --skip-training  # Skip training, use existing models
"""

import os
import sys
import argparse
from datetime import datetime

# Add current directory to path for helper_files imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num, description):
    """Print a step indicator."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 60)


# =============================================================================
# STEP 1: FEATURE ENGINEERING
# =============================================================================

def run_feature_engineering(data_dir):
    """Transform raw creature data into engineered features."""
    print_header("PHASE 1: FEATURE ENGINEERING")

    from helper_files import (
        CONDITIONS, PHASE2_FEATURES, PHASE2_PENALTIES, get_phase3_features,
        parse_cr, parse_hp, parse_ac, parse_speed, SIZE_ORDINAL_MAP,
        count_proficiencies, has_sense, parse_sense_range, parse_passive_perception,
        count_abilities, parse_legendary_actions, parse_attack_bonus, parse_save_dc,
        parse_dpr_from_json, parse_charge_bonus_attack, parse_legendary_actions_dpr,
        parse_legendary_conditions, extract_spellcaster_level,
        has_advantage_condition, has_disadvantage_condition, has_attackers_advantage,
        get_resistance_multiplier, get_immunity_multiplier, extract_family,
        get_baseline_hp, get_baseline_ac, get_baseline_attack, get_baseline_dpr,
        get_baseline_dc, get_baseline_size_ordinal, get_baseline_speed_ground,
        get_fly_speed_baseline, get_darkvision_baseline,
    )

    # Load raw data
    print_step(1, "Loading raw data")
    df = pd.read_csv(f'{data_dir}/dnd5e_monsters_from_json.csv')
    print(f"Loaded {len(df)} monsters")

    # Parse basic features
    print_step(2, "Parsing basic features")
    df['cr_numeric'] = df['Challenge_Rating'].apply(parse_cr)
    df['actual_hp'] = df['HP'].apply(parse_hp)
    df['ac_value'] = df['AC'].apply(parse_ac)

    # Parse speeds
    df['speed_ground'] = df['Speed'].apply(lambda x: parse_speed(x, 'ground'))
    df['speed_fly'] = df['Speed'].apply(lambda x: parse_speed(x, 'fly'))
    df['speed_swim'] = df['Speed'].apply(lambda x: parse_speed(x, 'swim'))
    df['speed_burrow'] = df['Speed'].apply(lambda x: parse_speed(x, 'burrow'))
    df['speed_climb'] = df['Speed'].apply(lambda x: parse_speed(x, 'climb'))
    df['max_speed'] = df[['speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb']].max(axis=1)
    df['movement_types_count'] = (df[['speed_ground', 'speed_fly', 'speed_swim', 'speed_burrow', 'speed_climb']] > 0).sum(axis=1)
    df['has_flying'] = (df['speed_fly'] > 0).astype(int)
    df['size_ordinal'] = df['Size'].map(SIZE_ORDINAL_MAP).fillna(2)
    print("  Speeds and size parsed")

    # Parse proficiencies
    df['save_proficiency_count'] = df['Saving_Throws'].apply(count_proficiencies)
    df['skill_proficiency_count'] = df['Skills'].apply(count_proficiencies)
    df['resistance_count'] = df['Resistances'].apply(count_proficiencies)
    df['immunity_count'] = df['Immunities'].apply(count_proficiencies)
    df['vulnerability_count'] = df['Vulnerabilities'].apply(count_proficiencies)
    df['condition_immunity_count'] = df['Condition_Immunities'].apply(count_proficiencies)
    print("  Proficiencies parsed")

    # Parse senses
    df['has_darkvision'] = df['Senses'].apply(lambda x: has_sense(x, 'darkvision'))
    df['darkvision_range'] = df['Senses'].apply(lambda x: parse_sense_range(x, 'darkvision'))
    df['has_blindsight'] = df['Senses'].apply(lambda x: has_sense(x, 'blindsight'))
    df['has_truesight'] = df['Senses'].apply(lambda x: has_sense(x, 'truesight'))
    df['has_tremorsense'] = df['Senses'].apply(lambda x: has_sense(x, 'tremorsense'))
    df['passive_perception'] = df['Senses'].apply(parse_passive_perception)
    print("  Senses parsed")

    # Parse ability counts
    df['action_count'] = df['Actions'].apply(count_abilities)
    df['reaction_count'] = df['Reactions'].apply(count_abilities)
    df['bonus_action_count'] = df['Bonus_Actions'].apply(count_abilities) if 'Bonus_Actions' in df.columns else 0
    df[['has_legendary_actions', 'legendary_action_count', 'legendary_actions_per_round']] = df['Legendary_Actions'].apply(
        lambda x: pd.Series(parse_legendary_actions(x))
    )
    print("  Ability counts parsed")

    # Parse combat stats
    print_step(3, "Parsing combat stats")
    df['highest_attack_bonus'] = df['Actions'].apply(parse_attack_bonus)
    combined_abilities = (df['Traits'].fillna('') + ' ' + df['Actions'].fillna('') + ' ' +
                         df['Reactions'].fillna('') + ' ' + df['Legendary_Actions'].fillna(''))
    df['highest_save_dc'] = combined_abilities.apply(parse_save_dc)

    # DC Overrides
    DC_OVERRIDES = {'Green Hag': 14}
    for creature, dc in DC_OVERRIDES.items():
        df.loc[df['Name'] == creature, 'highest_save_dc'] = dc

    # Parse DPR
    df['estimated_dpr'] = df['Actions'].apply(parse_dpr_from_json)
    df['charge_bonus_dpr'] = df.apply(lambda row: parse_charge_bonus_attack(row['Traits'], row['Actions']), axis=1)
    df['estimated_dpr'] = df['estimated_dpr'] + df['charge_bonus_dpr']
    df['legendary_dpr'] = df['Legendary_Actions'].apply(parse_legendary_actions_dpr)
    df['total_dpr'] = df['estimated_dpr'] + df['legendary_dpr']
    print(f"  DPR range: {df['total_dpr'].min():.1f} - {df['total_dpr'].max():.1f}")

    # Parse special traits
    print_step(4, "Parsing special traits")
    df['has_legendary_resistance'] = combined_abilities.str.contains('legendary resistance', case=False, na=False).astype(int)
    df['has_magic_resistance'] = combined_abilities.str.contains('magic resistance', case=False, na=False).astype(int)
    df['has_regeneration'] = combined_abilities.str.contains('regeneration', case=False, na=False).astype(int)
    df['has_spellcasting'] = combined_abilities.str.contains('spellcasting', case=False, na=False).astype(int)
    df['spellcaster_level'] = combined_abilities.apply(extract_spellcaster_level)
    df['has_grapple'] = combined_abilities.str.contains('grapple|grappled', case=False, na=False).astype(int)

    # Parse legendary conditions
    df['legendary_conditions'] = df['Legendary_Actions'].apply(parse_legendary_conditions)

    # Condition infliction features
    for condition in CONDITIONS:
        feature_name = f'inflicts_{condition}'
        df[feature_name] = combined_abilities.str.contains(condition, case=False, na=False).astype(int)
        df[feature_name] = df.apply(
            lambda row: 1 if (row[feature_name] == 1 or condition in row['legendary_conditions']) else 0,
            axis=1
        )

    # Inflicts prone
    df['inflicts_prone'] = combined_abilities.str.contains('prone', case=False, na=False).astype(int)
    df['inflicts_prone'] = df.apply(
        lambda row: 1 if (row['inflicts_prone'] == 1 or 'prone' in row['legendary_conditions']) else 0,
        axis=1
    )

    # Advantage/disadvantage conditions
    df['has_advantage_condition'] = df.apply(has_advantage_condition, axis=1)
    df['has_disadvantage_condition'] = df.apply(has_disadvantage_condition, axis=1)
    df['has_attackers_advantage'] = df.apply(has_attackers_advantage, axis=1)
    print(f"  Advantage conditions: {df['has_advantage_condition'].sum()}")

    # Calculate baselines
    print_step(5, "Calculating baselines and deviations")
    df['hp_baseline'] = df['cr_numeric'].apply(get_baseline_hp)
    df['ac_baseline'] = df['cr_numeric'].apply(get_baseline_ac)
    df['attack_baseline'] = df['cr_numeric'].apply(get_baseline_attack)
    df['dpr_baseline'] = df['cr_numeric'].apply(get_baseline_dpr)
    df['dc_baseline'] = df['cr_numeric'].apply(get_baseline_dc)
    df['size_ordinal_baseline'] = df['cr_numeric'].apply(get_baseline_size_ordinal)
    df['speed_ground_baseline'] = df['cr_numeric'].apply(get_baseline_speed_ground)
    df['fly_speed_baseline'] = df['cr_numeric'].apply(get_fly_speed_baseline)
    df['speed_fly_deviation'] = df.apply(
        lambda row: row['speed_fly'] - row['fly_speed_baseline'] if row['speed_fly'] > 0 else 0, axis=1
    )
    df['darkvision_baseline'] = df['cr_numeric'].apply(get_darkvision_baseline)
    df['darkvision_deviation'] = df.apply(
        lambda row: row['darkvision_range'] - row['darkvision_baseline'] if row['darkvision_range'] > 0 else 0, axis=1
    )

    # Calculate deviations
    df['ac_deviation'] = df['ac_value'] - df['ac_baseline']
    df['attack_deviation'] = df['highest_attack_bonus'] - df['attack_baseline']
    df['dpr_deviation'] = df['total_dpr'] - df['dpr_baseline']
    df['save_dc_deviation'] = df['highest_save_dc'] - df['dc_baseline']
    df['size_ordinal_deviation'] = df['size_ordinal'] - df['size_ordinal_baseline']
    df['speed_ground_deviation'] = df['speed_ground'] - df['speed_ground_baseline']
    print("  Deviations calculated")

    # Phase 1.5: Resistance/Immunity penalties
    print_step(6, "Applying Phase 1.5 resistance/immunity penalties")
    df_valid = df[df['actual_hp'] > 0].copy()
    df_valid['hp_after_phase1'] = df_valid['hp_baseline']
    # Calculate resistance/immunity multipliers (penalties applied after Phase 2)
    df_valid['resistance_multiplier'] = df_valid['cr_numeric'].apply(get_resistance_multiplier)
    df_valid['immunity_multiplier'] = df_valid['cr_numeric'].apply(get_immunity_multiplier)
    print(f"  Valid samples: {len(df_valid)} monsters with HP > 0")

    # Split by CR tier and apply Phase 2
    print_step(7, "Splitting by CR tier and applying Phase 2 penalties")
    df_cr1 = df_valid[df_valid['cr_numeric'] < 1.0].copy()
    df_cr2 = df_valid[(df_valid['cr_numeric'] >= 1.0) & (df_valid['cr_numeric'] <= 4.0)].copy()
    df_cr3 = df_valid[(df_valid['cr_numeric'] >= 5.0) & (df_valid['cr_numeric'] <= 10.0)].copy()
    df_cr4 = df_valid[(df_valid['cr_numeric'] >= 11.0) & (df_valid['cr_numeric'] <= 16.0)].copy()
    df_cr5 = df_valid[df_valid['cr_numeric'] > 16.0].copy()

    def apply_phase2_penalties(df_tier, tier_key):
        """Apply Phase 2 penalties and then resistance/immunity penalties."""
        penalties = PHASE2_PENALTIES[tier_key]

        # Phase 2: Combat stat penalties starting from hp_after_phase1
        df_tier['hp_after_phase2'] = df_tier['hp_after_phase1'].copy()
        for feature, penalty in penalties.items():
            if feature in df_tier.columns:
                df_tier['hp_after_phase2'] += df_tier[feature] * penalty

        # Apply resistance/immunity penalties AFTER Phase 2
        df_tier['resistance_penalty'] = (
            df_tier['resistance_multiplier'] *
            df_tier['hp_after_phase2'] *
            (df_tier['resistance_count'] > 0)
        )
        df_tier['immunity_penalty'] = (
            df_tier['immunity_multiplier'] *
            df_tier['hp_after_phase2'] *
            (df_tier['immunity_count'] > 0)
        )
        df_tier['total_defensive_penalty'] = (
            df_tier['immunity_penalty'] + df_tier['resistance_penalty']
        ).clip(upper=0.75 * df_tier['hp_after_phase2'])

        df_tier['hp_after_resist_immun_penalty'] = df_tier['hp_after_phase2'] - df_tier['total_defensive_penalty']

        # Calculate scaled features from hp_after_resist_immun_penalty
        df_tier['has_legendary_resistance_scaled'] = df_tier['has_legendary_resistance'] * df_tier['hp_after_resist_immun_penalty']
        df_tier['has_magic_resistance_scaled'] = df_tier['has_magic_resistance'] * df_tier['hp_after_resist_immun_penalty']
        df_tier['has_regeneration_scaled'] = df_tier['has_regeneration'] * df_tier['hp_after_resist_immun_penalty']

        # Calculate residual HP from final value
        df_tier['residual_hp'] = df_tier['actual_hp'] - df_tier['hp_after_resist_immun_penalty']
        df_tier['family'] = df_tier['Name'].apply(extract_family)
        df_tier['cr_tier'] = tier_key
        return df_tier

    df_cr1 = apply_phase2_penalties(df_cr1, 'cr1')
    df_cr2 = apply_phase2_penalties(df_cr2, 'cr2')
    df_cr3 = apply_phase2_penalties(df_cr3, 'cr3')
    df_cr4 = apply_phase2_penalties(df_cr4, 'cr4')
    df_cr5 = apply_phase2_penalties(df_cr5, 'cr5')

    print(f"  CR < 1:    {len(df_cr1)} monsters")
    print(f"  CR 1-4:    {len(df_cr2)} monsters")
    print(f"  CR 5-10:   {len(df_cr3)} monsters")
    print(f"  CR 11-16:  {len(df_cr4)} monsters")
    print(f"  CR > 16:   {len(df_cr5)} monsters")

    # Combine and save
    print_step(8, "Saving engineered features")
    df_engineered = pd.concat([df_cr1, df_cr2, df_cr3, df_cr4, df_cr5], ignore_index=True)
    df_engineered = df_engineered.sort_values('cr_numeric')

    output_path = 'helper_files/engineered_features.csv'
    df_engineered.to_csv(output_path, index=False)
    print(f"  Saved {len(df_engineered)} monsters with {len(df_engineered.columns)} features")
    print(f"  Output: {output_path}")

    return df_engineered


# =============================================================================
# STEP 2: MODEL TRAINING
# =============================================================================

def run_model_training(df):
    """Train the 5-tier HP prediction models."""
    print_header("PHASE 2: MODEL TRAINING")

    from helper_files import (
        get_phase3_features, train_constrained_model, ConstrainedModel,
        calculate_r2, calculate_mae, save_model,
    )

    phase3_features = get_phase3_features()
    print(f"Phase 3 features: {len(phase3_features)}")

    # Split by CR tier
    print_step(1, "Splitting data by CR tier")
    tiers = {
        'cr1': df[df['cr_tier'] == 'cr1'].copy(),
        'cr2': df[df['cr_tier'] == 'cr2'].copy(),
        'cr3': df[df['cr_tier'] == 'cr3'].copy(),
        'cr4': df[df['cr_tier'] == 'cr4'].copy(),
        'cr5': df[df['cr_tier'] == 'cr5'].copy(),
    }

    for tier, tier_df in tiers.items():
        print(f"  {tier}: {len(tier_df)} monsters")

    # Train/test split function
    def manual_train_test_split(df_tier, test_ratio=0.2, random_state=42):
        np.random.seed(random_state)
        simple_families = ['beast', 'humanoid', 'giant']
        simple_mask = df_tier['family'].isin(simple_families)
        complex_families = df_tier[~simple_mask]['family'].unique()
        np.random.shuffle(complex_families)
        n_test = max(1, int(len(complex_families) * test_ratio))
        test_families = set(complex_families[:n_test])
        train_mask = simple_mask | ~df_tier['family'].isin(test_families)
        return df_tier[train_mask], df_tier[~train_mask]

    # Train models
    print_step(2, "Training models")
    results = {}
    models = {}
    scalers = {}

    tier_labels = {
        'cr1': 'CR < 1',
        'cr2': 'CR 1-4',
        'cr3': 'CR 5-10',
        'cr4': 'CR 11-16',
        'cr5': 'CR > 16',
    }

    for tier, tier_df in tiers.items():
        print(f"\n  Training {tier_labels[tier]} model...")

        # Split data (use all data for small tiers)
        if len(tier_df) < 30:
            train_df, test_df = tier_df, tier_df
        else:
            train_df, test_df = manual_train_test_split(tier_df)

        # Prepare features
        X_train = train_df[phase3_features].fillna(0).values
        y_train = train_df['residual_hp'].values
        X_test = test_df[phase3_features].fillna(0).values
        y_test = test_df['residual_hp'].values

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train constrained model
        coefficients, intercept = train_constrained_model(X_train_scaled, y_train, phase3_features, scaler)
        model = ConstrainedModel(coefficients, intercept)

        # Evaluate (residual is based on hp_after_resist_immun_penalty)
        y_pred_residual = model.predict(X_test_scaled)
        y_pred_hp = test_df['hp_after_resist_immun_penalty'].values + y_pred_residual
        y_actual_hp = test_df['actual_hp'].values

        r2 = calculate_r2(y_actual_hp, y_pred_hp)
        mae = calculate_mae(y_actual_hp, y_pred_hp)

        print(f"    Training samples: {len(train_df)}")
        print(f"    Test R²:  {r2:.4f}")
        print(f"    Test MAE: {mae:.2f} HP")

        results[tier] = {'train_count': len(train_df), 'test_r2': r2, 'test_mae': mae}
        models[tier] = model
        scalers[tier] = scaler

    # Save models
    print_step(3, "Saving models")
    os.makedirs('../pickled_models', exist_ok=True)

    for tier in tiers.keys():
        filepath = f'../pickled_models/hp_model_{tier}.pkl'
        save_model(models[tier], scalers[tier], phase3_features, filepath)
        print(f"  Saved {tier} model to {filepath}")

    return models, scalers, results


# =============================================================================
# STEP 3: MODEL ANALYSIS
# =============================================================================

def run_model_analysis(df, models, scalers, data_dir):
    """Generate predictions and export results."""
    print_header("PHASE 3: MODEL ANALYSIS")

    from helper_files import (
        get_phase3_features, PHASE2_PENALTIES, add_percentile_by_cr,
    )

    phase3_features = get_phase3_features()

    # Generate predictions
    print_step(1, "Generating predictions")

    def get_prediction_for_creature(row):
        tier = row['cr_tier']
        X = np.array([[row.get(f, 0) if pd.notna(row.get(f, 0)) else 0 for f in phase3_features]])
        X_scaled = scalers[tier].transform(X)
        residual_pred = models[tier].predict(X_scaled)[0]
        # Residual is based on hp_after_resist_immun_penalty
        return row['hp_after_resist_immun_penalty'] + residual_pred

    df['predicted_hp'] = df.apply(get_prediction_for_creature, axis=1)
    df['hp_delta'] = df['predicted_hp'] - df['actual_hp']
    df['hp_delta_pct'] = (df['hp_delta'] / df['actual_hp']) * 100
    df = add_percentile_by_cr(df)

    print(f"  Mean HP Error: {df['hp_delta'].mean():.1f} HP")
    print(f"  Mean Absolute Error: {df['hp_delta'].abs().mean():.1f} HP")
    print(f"  Mean Absolute % Error: {df['hp_delta_pct'].abs().mean():.1f}%")

    # Export predictions
    print_step(2, "Exporting predictions")
    export_columns = [
        'Name', 'Type', 'Size', 'Challenge_Rating', 'cr_numeric', 'cr_tier',
        'HP', 'actual_hp', 'AC', 'ac_value',
        'predicted_hp', 'hp_delta', 'hp_delta_pct', 'hp_delta_pct_percentile',
        'hp_baseline', 'ac_baseline', 'attack_baseline', 'dpr_baseline', 'dc_baseline',
        'highest_attack_bonus', 'highest_save_dc', 'estimated_dpr', 'legendary_dpr', 'total_dpr',
        'ac_deviation', 'attack_deviation', 'dpr_deviation', 'save_dc_deviation',
        'hp_after_phase2', 'hp_after_resist_immun_penalty', 'residual_hp',
    ]
    export_cols = [c for c in export_columns if c in df.columns]
    export_df = df[export_cols].sort_values('cr_numeric')
    export_df.to_csv(f'{data_dir}/engineered_features.csv', index=False)
    print(f"  Exported {len(export_df)} monsters to {data_dir}/engineered_features.csv")

    # Calculate feature contributions
    print_step(3, "Calculating feature contributions")

    def calculate_feature_contributions(row):
        tier = row['cr_tier']
        penalties = PHASE2_PENALTIES[tier]

        contributions = {
            'Name': row['Name'],
            'CR': row['cr_numeric'],
            'actual_hp': row['actual_hp'],
            'predicted_hp': row['predicted_hp'],
            'hp_error': row['hp_delta'],
            'hp_error_pct': row['hp_delta_pct'],
            'hp_baseline': row['hp_baseline'],
            'hp_after_phase2': row['hp_after_phase2'],
            'hp_after_resist_immun_penalty': row['hp_after_resist_immun_penalty'],
        }

        # Phase 2 contributions
        contributions['phase2_ac_contribution'] = row['ac_deviation'] * penalties.get('ac_deviation', 0)
        contributions['phase2_attack_contribution'] = row['attack_deviation'] * penalties.get('attack_deviation', 0)
        contributions['phase2_dpr_contribution'] = row['dpr_deviation'] * penalties.get('dpr_deviation', 0)
        contributions['phase2_save_dc_contribution'] = row['save_dc_deviation'] * penalties.get('save_dc_deviation', 0)
        contributions['phase2_flying_contribution'] = row['has_flying'] * penalties.get('has_flying', 0)

        # Phase 3 contributions
        X = np.array([[row.get(f, 0) for f in phase3_features]])
        X = np.nan_to_num(X, 0)
        X_scaled = scalers[tier].transform(X)[0]
        coefs = models[tier].coef_

        phase3_total = 0
        for i, feature in enumerate(phase3_features):
            contrib = X_scaled[i] * coefs[i]
            contributions[f'phase3_{feature}'] = contrib
            phase3_total += contrib

        contributions['phase3_intercept'] = models[tier].intercept_
        contributions['phase3_total_contribution'] = phase3_total + contributions['phase3_intercept']

        return pd.Series(contributions)

    contributions_df = df.apply(calculate_feature_contributions, axis=1)
    contributions_df.to_csv(f'{data_dir}/feature_contributions.csv', index=False)
    print(f"  Exported contributions to {data_dir}/feature_contributions.csv")

    # Summary by tier
    print_step(4, "Summary by CR tier")
    tier_labels = {
        'cr1': 'CR < 1',
        'cr2': 'CR 1-4',
        'cr3': 'CR 5-10',
        'cr4': 'CR 11-16',
        'cr5': 'CR > 16',
    }

    for tier in ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']:
        tier_df = df[df['cr_tier'] == tier]
        mae = tier_df['hp_delta'].abs().mean()
        mape = tier_df['hp_delta_pct'].abs().mean()
        print(f"  {tier_labels[tier]:12s}: MAE={mae:6.1f} HP, MAPE={mape:5.1f}%")

    return df, contributions_df


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Execute HP prediction model pipeline end-to-end')
    parser.add_argument('--skip-training', action='store_true',
                        help='Skip training, use existing models')
    parser.add_argument('--data-dir', default='../data',
                        help='Data directory (default: ../data)')
    args = parser.parse_args()

    start_time = datetime.now()
    print_header(f"HP PREDICTION MODEL PIPELINE")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data directory: {args.data_dir}")

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Step 1: Feature Engineering
    df = run_feature_engineering(args.data_dir)

    # Step 2: Model Training
    if args.skip_training:
        print_header("PHASE 2: MODEL TRAINING (SKIPPED)")
        print("Loading existing models...")
        from helper_files import load_model, get_phase3_features

        models = {}
        scalers = {}
        for tier in ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']:
            data = load_model(f'../pickled_models/hp_model_{tier}.pkl')
            models[tier] = data['model']
            scalers[tier] = data['scaler']
            print(f"  Loaded {tier} model")
        results = None
    else:
        models, scalers, results = run_model_training(df)

    # Step 3: Model Analysis
    df, contributions_df = run_model_analysis(df, models, scalers, args.data_dir)

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    print_header("PIPELINE COMPLETE")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration.total_seconds():.1f} seconds")
    print(f"\nOutputs:")
    print(f"  - helper_files/engineered_features.csv")
    print(f"  - ../pickled_models/hp_model_cr*.pkl")
    print(f"  - {args.data_dir}/engineered_features.csv")
    print(f"  - {args.data_dir}/feature_contributions.csv")

    if results:
        print(f"\nModel Performance:")
        for tier in ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']:
            r = results[tier]
            print(f"  {tier}: R²={r['test_r2']:.4f}, MAE={r['test_mae']:.1f} HP")


if __name__ == '__main__':
    main()
