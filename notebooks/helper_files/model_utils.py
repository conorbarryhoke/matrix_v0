"""
Model training and basic analysis utilities for the HP prediction model.

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
