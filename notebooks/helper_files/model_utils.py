"""
Model training and analysis utilities for the HP prediction model.

This module contains functions for training constrained regression models,
evaluating predictions, and investigating individual creature predictions.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, Bounds
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from .feature_config import CONDITIONS, PHASE2_PENALTIES, get_cr_tier, get_phase3_features


# =============================================================================
# BOOLEAN FEATURES (CONSTRAINED TO NON-POSITIVE)
# =============================================================================

# Base boolean features that must have non-positive coefficients
BOOLEAN_FEATURES_BASE = [
    'has_darkvision', 'has_blindsight', 'has_truesight', 'has_tremorsense',
    'has_spellcasting', 'has_grapple'
]


def get_boolean_features():
    """Return the full list of boolean features that must have non-positive coefficients."""
    features = BOOLEAN_FEATURES_BASE.copy()
    for condition in CONDITIONS:
        features.append(f'inflicts_{condition}')
    return features


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_constrained_model(X_scaled, y, feature_names, scaler=None):
    """
    Train a linear regression model with constraints:
    - No intercept (coefficients only)
    - Boolean features must have non-positive coefficients

    Args:
        X_scaled: Scaled feature matrix (numpy array)
        y: Target variable (residual HP)
        feature_names: List of feature names corresponding to X columns
        scaler: StandardScaler instance (optional, for reference)

    Returns:
        tuple: (coefficients, intercept=0.0)
    """
    n_features = X_scaled.shape[1]
    boolean_features = get_boolean_features()

    # Get indices of boolean features
    boolean_indices = [i for i, feat in enumerate(feature_names) if feat in boolean_features]

    # Objective: minimize sum of squared errors (standard OLS)
    def objective(coef):
        y_pred = X_scaled @ coef
        return np.sum((y - y_pred) ** 2)

    # Gradient for faster optimization
    def gradient(coef):
        y_pred = X_scaled @ coef
        return -2 * X_scaled.T @ (y - y_pred)

    # Set up bounds: boolean features must be <= 0, others unbounded
    lower_bounds = [-np.inf] * n_features
    upper_bounds = [np.inf] * n_features

    for idx in boolean_indices:
        upper_bounds[idx] = 0  # Constrain boolean features to be <= 0

    bounds = Bounds(lower_bounds, upper_bounds)

    # Initial guess: standard OLS solution (for faster convergence)
    try:
        initial_coef = np.linalg.lstsq(X_scaled, y, rcond=None)[0]
    except:
        initial_coef = np.zeros(n_features)

    # Optimize
    result = minimize(
        objective,
        initial_coef,
        method='L-BFGS-B',
        jac=gradient,
        bounds=bounds,
        options={'maxiter': 10000, 'ftol': 1e-10}
    )

    if not result.success:
        print(f"   Warning: Optimization: {result.message}")

    return result.x, 0.0  # Return coefficients and intercept=0


def train_unconstrained_model(X_scaled, y):
    """
    Train a standard linear regression model (no constraints).

    Args:
        X_scaled: Scaled feature matrix
        y: Target variable

    Returns:
        LinearRegression: Fitted model
    """
    model = LinearRegression(fit_intercept=True)
    model.fit(X_scaled, y)
    return model


# =============================================================================
# PREDICTION HELPERS
# =============================================================================

class ConstrainedModel:
    """
    A simple model class that mimics sklearn's interface for constrained models.
    """

    def __init__(self, coefficients, intercept=0.0):
        self.coef_ = np.array(coefficients)
        self.intercept_ = intercept

    def predict(self, X):
        """Predict using the linear model."""
        return X @ self.coef_ + self.intercept_


def get_prediction(row, models, scalers, phase3_features):
    """
    Get HP prediction for a single creature.

    Args:
        row: DataFrame row or dict with creature features
        models: Dict of models keyed by tier (cr1, cr2, etc.)
        scalers: Dict of scalers keyed by tier
        phase3_features: List of Phase 3 feature names

    Returns:
        float: Predicted HP
    """
    cr = row.get('cr_numeric', 0)
    tier = get_cr_tier(cr)

    # Get features
    X = np.array([[row.get(f, 0) for f in phase3_features]])

    # Fill NaN with 0
    X = np.nan_to_num(X, 0)

    # Scale and predict
    X_scaled = scalers[tier].transform(X)
    residual_pred = models[tier].predict(X_scaled)[0]

    return row.get('hp_after_phase2', 0) + residual_pred


def add_percentile_by_cr(df):
    """
    Add percentile ranking of absolute hp_delta_pct within each CR bucket.

    Args:
        df: DataFrame with hp_delta_pct column

    Returns:
        DataFrame with hp_delta_pct_percentile column added
    """
    df = df.copy()
    df['hp_delta_pct_percentile'] = 0.0

    cr_buckets = [
        (df['cr_numeric'] < 1.0, 'cr1'),
        ((df['cr_numeric'] >= 1.0) & (df['cr_numeric'] <= 4.0), 'cr2'),
        ((df['cr_numeric'] > 4.0) & (df['cr_numeric'] <= 10.0), 'cr3'),
        ((df['cr_numeric'] > 10.0) & (df['cr_numeric'] <= 16.0), 'cr4'),
        (df['cr_numeric'] > 16.0, 'cr5'),
    ]

    for mask, tier in cr_buckets:
        if mask.any():
            abs_pct = df.loc[mask, 'hp_delta_pct'].abs()
            df.loc[mask, 'hp_delta_pct_percentile'] = abs_pct.rank(pct=True) * 100

    return df


# =============================================================================
# EVALUATION METRICS
# =============================================================================

def calculate_r2(y_true, y_pred):
    """Calculate R-squared (coefficient of determination)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0


def calculate_mae(y_true, y_pred):
    """Calculate Mean Absolute Error."""
    return np.mean(np.abs(y_true - y_pred))


def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def evaluate_model(y_true, y_pred, label=""):
    """
    Print evaluation metrics for a model.

    Args:
        y_true: Actual values
        y_pred: Predicted values
        label: Optional label for the model
    """
    r2 = calculate_r2(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    mape = calculate_mape(y_true, y_pred)

    if label:
        print(f"\n{label}:")
    print(f"   R²:   {r2:.4f}")
    print(f"   MAE:  {mae:.2f} HP")
    print(f"   MAPE: {mape:.1f}%")

    return {'r2': r2, 'mae': mae, 'mape': mape}


# =============================================================================
# INVESTIGATION HELPERS
# =============================================================================

def investigate_creature(creature_name, export_df, contributions_df):
    """
    Display a streamlined breakdown of a creature's HP prediction.
    Shows actual features and their HP impacts side-by-side.

    Args:
        creature_name: Name of the creature to investigate
        export_df: DataFrame with creature features
        contributions_df: DataFrame with feature contributions
    """
    # Get creature data from both dataframes
    creature_contrib = contributions_df[contributions_df['Name'] == creature_name]
    creature_export = export_df[export_df['Name'] == creature_name]

    if len(creature_contrib) == 0:
        print(f"Creature '{creature_name}' not found!")
        return

    creature_contrib = creature_contrib.iloc[0]
    creature_export = creature_export.iloc[0]

    print("=" * 80)
    print(f"  {creature_name.upper()} (CR {creature_contrib['CR']})")
    print("=" * 80)
    print()

    # Summary
    print(f"Actual HP:        {creature_contrib['actual_hp']:>8.0f}")
    print(f"Predicted HP:     {creature_contrib['predicted_hp']:>8.0f}")
    print(f"Error:            {creature_contrib['hp_error']:>8.0f}  ({creature_contrib['hp_error_pct']:>6.1f}%)")
    print()
    print("-" * 80)

    # Phase 1: Baseline
    print(f"\nPHASE 1: CR BASELINE")
    print(f"  HP Baseline (CR {creature_contrib['CR']}):                          {creature_contrib['hp_baseline']:>8.0f}")

    # Phase 1.5: Resistances/Immunities
    print(f"\nPHASE 1.5: RESISTANCES & IMMUNITIES")
    res_penalty = creature_contrib.get('phase1_5_resistance_penalty', 0)
    imm_penalty = creature_contrib.get('phase1_5_immunity_penalty', 0)

    if res_penalty != 0 or imm_penalty != 0:
        print(f"  Resistance Penalty:                              {res_penalty:>8.0f}")
        print(f"  Immunity Penalty:                                {imm_penalty:>8.0f}")
        print(f"  Total Penalty:                                   {creature_contrib.get('phase1_5_total_penalty', 0):>8.0f}")
    else:
        print(f"  No resistances or immunities")
    print(f"  HP after Phase 1.5:                              {creature_contrib['hp_after_phase1_5']:>8.0f}")

    # Phase 2: Combat Stats
    print(f"\nPHASE 2: COMBAT STATS")
    combat_stats = [
        ('AC Contribution', 'phase2_ac_contribution'),
        ('Attack Bonus Contribution', 'phase2_attack_contribution'),
        ('DPR Contribution', 'phase2_dpr_contribution'),
        ('Save DC Contribution', 'phase2_save_dc_contribution'),
        ('Flying Contribution', 'phase2_flying_contribution'),
        ('Advantage Condition', 'phase2_advantage_contribution'),
        ('Disadvantage Condition', 'phase2_disadvantage_contribution'),
        ('Attackers Have Advantage', 'phase2_attackers_advantage_contribution'),
        ('Inflicts Prone', 'phase2_prone_contribution'),
    ]

    for label, col in combat_stats:
        val = creature_contrib.get(col, 0)
        if val != 0:
            print(f"  {label:<45} {val:>8.0f}")

    print(f"  {'-' * 53}")
    print(f"  Phase 2 Total:                                   {creature_contrib.get('phase2_total_contribution', 0):>8.0f}")
    print(f"  HP after Phase 2:                                {creature_contrib['hp_after_phase2']:>8.0f}")

    # Phase 3: Individual Features
    print(f"\nPHASE 3: INDIVIDUAL FEATURES")

    # Get all phase3 columns
    phase3_cols = [col for col in contributions_df.columns
                   if col.startswith('phase3_')
                   and col != 'phase3_total_contribution'
                   and col != 'phase3_intercept']

    for col in phase3_cols:
        feature_name = col.replace('phase3_', '')
        hp_impact = creature_contrib.get(col, 0)

        # Get the actual feature value
        if feature_name in creature_export.index:
            feature_value = creature_export[feature_name]
        else:
            feature_value = 'N/A'

        try:
            val_str = f"{float(feature_value):.1f}"
        except:
            val_str = str(feature_value)

        print(f"  Feature: {feature_name:<35} value: {val_str:>6}  hp impact: {hp_impact:>6.0f}")

    print(f"\n  Intercept:                                       {creature_contrib.get('phase3_intercept', 0):>8.0f}")
    print(f"  {'-' * 53}")
    print(f"  Phase 3 Total:                                   {creature_contrib.get('phase3_total_contribution', 0):>8.0f}")

    print()
    print("=" * 80)
    print(f"  FINAL PREDICTED HP:                              {creature_contrib['predicted_hp']:>8.0f}")
    print(f"  ACTUAL HP:                                       {creature_contrib['actual_hp']:>8.0f}")
    print(f"  ERROR:                                           {creature_contrib['hp_error']:>8.0f}  ({creature_contrib['hp_error_pct']:>6.1f}%)")
    print("=" * 80)


# =============================================================================
# SUMMARY FUNCTIONS
# =============================================================================

def summarize_model_performance(results):
    """
    Print a summary of model performance across all CR tiers.

    Args:
        results: Dict with keys 'cr1' through 'cr5', each containing
                 'train_count', 'test_r2', 'test_mae'
    """
    print("\n" + "=" * 80)
    print("5-BUCKET HP MODEL TRAINING COMPLETE")
    print("=" * 80)

    tier_labels = {
        'cr1': 'CR < 1',
        'cr2': 'CR 1-4',
        'cr3': 'CR 5-10',
        'cr4': 'CR 11-16',
        'cr5': 'CR > 16',
    }

    print("\nMODEL PERFORMANCE SUMMARY:")
    for tier in ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']:
        r = results.get(tier, {})
        print(f"\n   {tier_labels[tier]} Model:")
        print(f"      Training samples: {r.get('train_count', 0)}")
        print(f"      Test R²:  {r.get('test_r2', 0):.4f}")
        print(f"      Test MAE: {r.get('test_mae', 0):.2f} HP")

    print("\n" + "=" * 80)
    print("All 5 models trained successfully!")
    print("=" * 80)



# =============================================================================
# MODEL PERSISTENCE
# =============================================================================

def save_model(
        model, scaler, feature_names, train_count, test_r2, test_mae, filepath):
    """
    Save a model, scaler, and feature names to a pickle file.

    Args:
        model: Trained model (ConstrainedModel or sklearn model)
        scaler: StandardScaler instance
        feature_names: List of feature names
        filepath: Path to save the pickle file
    """
    import pickle
    with open(filepath, 'wb') as f:
        pickle.dump({
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names,
            'train_count': train_count,
            'test_r2': test_r2,
            'test_mae': test_mae,
        }, f)


def load_model(filepath):
    """
    Load a model, scaler, and feature names from a pickle file.

    Args:
        filepath: Path to the pickle file

    Returns:
        dict: Dictionary with 'model', 'scaler', 'feature_names' keys
    """
    import pickle
    with open(filepath, 'rb') as f:
        return pickle.load(f)
