



def train_tier_model(train_df, test_df, tier_name, phase3_features):
    """Train a model for a single CR tier."""
    print(f"\n{'='*60}")
    print(f"Training {tier_name} model...")
    print(f"{'='*60}")
    
    # Prepare features
    X_train = train_df[phase3_features].fillna(0).values
    y_train = train_df['residual_hp'].values
    
    X_test = test_df[phase3_features].fillna(0).values
    y_test = test_df['residual_hp'].values
    
    # Scale features (with_mean=False to preserve zero values)
    scaler = StandardScaler(with_mean=False)
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train constrained model
    coefficients, intercept = train_constrained_model(
        X_train_scaled, y_train, phase3_features, scaler
    )
    
    # Create model object
    model = ConstrainedModel(coefficients, intercept)
    
    # Evaluate on test set
    y_pred_residual = model.predict(X_test_scaled)
    
    # Calculate full HP predictions
    y_pred_hp = test_df['hp_after_phase2'].values + y_pred_residual
    y_actual_hp = test_df['actual_hp'].values
    
    # Calculate metrics
    r2 = calculate_r2(y_actual_hp, y_pred_hp)
    mae = calculate_mae(y_actual_hp, y_pred_hp)
    
    print(f"\n{tier_name} Results:")
    print(f"   Training samples: {len(y_train)}")
    print(f"   Test R²:  {r2:.4f}")
    print(f"   Test MAE: {mae:.2f} HP")
    
    return {
        'model': model,
        'scaler': scaler,
        'train_count': len(y_train),
        'test_r2': r2,
        'test_mae': mae,
    }