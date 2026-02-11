"""
Adanced analysis and investigation utilies for model performances

"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from .feature_config import (
    CR_TIERS, PHASE2_FEATURES, PHASE2_PENALTIES,
    DMG_FEATURE_NAMES, DMG_AC_ADJUSTMENTS, DMG_ATTACK_ADJUSTMENTS,
    DMG_DPR_ADJUSTMENTS, DMG_HP_PER_USE, DMG_HP_BY_TIER,
    DMG_HP_PERCENTAGE, DMG_HP_MULTIPLIER,
    get_cr_tier,
)
from matplotlib.patches import Patch

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _is_binary_feature(analysis_dfs, feature_name):
    """Check if feature has only 0/1 or True/False values across all tiers."""
    all_values = []
    for tier_df in analysis_dfs.values():
        if feature_name in tier_df.columns:
            all_values.extend(tier_df[feature_name].dropna().tolist())
    unique_vals = set(all_values)
    return unique_vals <= {0, 1, True, False, 0.0, 1.0}

# =============================================================================
# INVESTIGATION HELPERS
# =============================================================================

def _get_costed_features_detail(creature_export):
    """Build per-category lists of detected DMG features and their costs."""
    cr = creature_export.get('cr_numeric', 0)
    tier = get_cr_tier(cr)
    hp_baseline = creature_export.get('hp_baseline', 0)

    details = {'ac': [], 'attack': [], 'dpr': [], 'hp': []}

    # AC: derive contributions by working backwards from total feature_ac
    total_feature_ac = creature_export.get('feature_ac', 0)
    accounted_ac = 0

    # DMG_AC_ADJUSTMENTS contributions (keys use spaces)
    for feat_name, cost in DMG_AC_ADJUSTMENTS.items():
        col = f'feature_{feat_name.replace(" ", "_")}'
        if creature_export.get(col, 0) == 1:
            details['ac'].append((feat_name.replace(' ', '_'), f'+{cost}'))
            accounted_ac += cost

    # Saving throws contribution
    save_count = creature_export.get('save_proficiency_count', 0)
    if save_count >= 5:
        details['ac'].append((f'saving_throws ({int(save_count)} saves)', '+4'))
        accounted_ac += 4
    elif save_count >= 3:
        details['ac'].append((f'saving_throws ({int(save_count)} saves)', '+2'))
        accounted_ac += 2

    # Flying: attribute remaining AC to flying (avoids needing _has_ranged_damage)
    if creature_export.get('has_flying', 0) == 1:
        flying_ac = total_feature_ac - accounted_ac
        if flying_ac > 0:
            details['ac'].append((f'flying (CR {int(cr)})', f'+{flying_ac}'))
        elif cr > 10:
            details['ac'].append(('flying (CR>10, no cost)', '+0'))
        else:
            details['ac'].append(('flying (no ranged, no cost)', '+0'))

    # Attack costs from DMG_ATTACK_ADJUSTMENTS (keys use spaces)
    for feat_name, cost in DMG_ATTACK_ADJUSTMENTS.items():
        col = f'feature_{feat_name.replace(" ", "_")}'
        if creature_export.get(col, 0) == 1:
            details['attack'].append((feat_name.replace(' ', '_'), f'+{cost}'))

    # DPR costs from DMG_DPR_ADJUSTMENTS (keys use snake_case)
    for feat_name, cost in DMG_DPR_ADJUSTMENTS.items():
        col = f'feature_{feat_name}'
        if creature_export.get(col, 0) == 1:
            details['dpr'].append((feat_name, f'+{cost}/round'))

    # HP costs
    for feat_name, tier_values in DMG_HP_PER_USE.items():
        col = f'feature_{feat_name}'
        if creature_export.get(col, 0) == 1:
            per_use = tier_values.get(tier, 0)
            details['hp'].append((feat_name, f'{per_use}/use'))

    for feat_name, tier_values in DMG_HP_BY_TIER.items():
        col = f'feature_{feat_name}'
        if creature_export.get(col, 0) == 1:
            val = tier_values.get(tier, 0)
            details['hp'].append((feat_name, f'{val}'))

    for feat_name, pct in DMG_HP_PERCENTAGE.items():
        col = f'feature_{feat_name}'
        if creature_export.get(col, 0) == 1:
            if cr <= 10:
                val = hp_baseline * pct / (1 + pct)
                details['hp'].append((feat_name, f'{val:.0f} ({pct:.0%} of baseline)'))
            else:
                details['hp'].append((feat_name, f'0 (CR>{10}, no cost)'))

    for feat_name, mult in DMG_HP_MULTIPLIER.items():
        col = f'feature_{feat_name}'
        if creature_export.get(col, 0) == 1:
            val = hp_baseline * (1 - 1 / mult)
            details['hp'].append((feat_name, f'{val:.0f} ({mult}x multiplier)'))

    if creature_export.get('feature_regeneration', 0) == 1:
        details['hp'].append(('regeneration', 'regen/round x 3'))

    return details


def investigate_creature(creature_name, export_df, contributions_df):
    """
    Display a detailed breakdown of a creature's HP prediction.
    Shows Phase 1 (baseline + feature HP), Phase 2 (deviation breakdown,
    costed DMG features, HP penalties), resistance/immunity, and Phase 3.

    Args:
        creature_name: Name of the creature to investigate
        export_df: DataFrame with creature features (4-layer columns, DMG flags)
        contributions_df: DataFrame with feature contributions (HP impacts)
    """
    # Get creature data from both dataframes
    creature_contrib = contributions_df[contributions_df['Name'] == creature_name]
    creature_export = export_df[export_df['Name'] == creature_name]

    if len(creature_contrib) == 0:
        print(f"Creature '{creature_name}' not found!")
        return

    creature_contrib = creature_contrib.iloc[0]
    creature_export = creature_export.iloc[0]

    cr = creature_contrib['CR']
    hp_baseline = creature_contrib['hp_baseline']
    feature_hp = creature_contrib.get('feature_hp', 0)
    hp_after_phase1 = hp_baseline - feature_hp

    print("=" * 80)
    print(f"  {creature_name.upper()} (CR {cr})")
    print("=" * 80)
    print()

    # Summary
    print(f"Actual HP:        {creature_contrib['actual_hp']:>8.0f}")
    print(f"Predicted HP:     {creature_contrib['predicted_hp']:>8.0f}")
    print(f"Error:            {creature_contrib['hp_error']:>8.0f}  ({creature_contrib['hp_error_pct']:>6.1f}%)")
    print()
    print("-" * 80)

    # ── Phase 1: Baseline ────────────────────────────────────────────────────
    print(f"\nPHASE 1: CR BASELINE")
    print(f"  HP Baseline (CR {cr}):                          {hp_baseline:>8.0f}")
    if feature_hp != 0:
        print(f"  Feature HP (DMG adjustments):                  {-feature_hp:>8.0f}")
    print(f"  HP after Phase 1:                                {hp_after_phase1:>8.0f}")

    # ── Phase 2: Combat Stats ────────────────────────────────────────────────
    print(f"\nPHASE 2: COMBAT STATS")

    # Deviation Breakdown table
    print(f"\n  Deviation Breakdown:")
    print(f"    {'Stat':<12} {'Estimated':>9}  {'Feature':>8}  {'Total':>7}  {'Baseline':>8}  {'Deviation':>9}")
    print(f"    {'-'*60}")

    # AC row
    ac_est = creature_export.get('ac_value', 0)
    ac_feat = creature_export.get('feature_ac', 0)
    ac_total = creature_export.get('total_ac', 0)
    ac_base = creature_export.get('ac_baseline', 0)
    ac_dev = creature_export.get('ac_deviation', 0)
    print(f"    {'AC':<12} {ac_est:>9.0f}  {ac_feat:>+8.0f}  {ac_total:>7.0f}  {ac_base:>8.0f}  {ac_dev:>+9.0f}")

    # Attack row
    atk_est = creature_export.get('highest_attack_bonus', 0)
    atk_feat = creature_export.get('feature_attack', 0)
    atk_total = creature_export.get('total_attack', 0)
    atk_base = creature_export.get('attack_baseline', 0)
    atk_dev = creature_export.get('attack_deviation', 0)
    print(f"    {'Attack':<12} {atk_est:>9.0f}  {atk_feat:>+8.0f}  {atk_total:>7.0f}  {atk_base:>8.0f}  {atk_dev:>+9.0f}")

    # DPR row
    dpr_est = creature_export.get('estimated_dpr', 0)
    dpr_feat = creature_export.get('feature_dpr', 0)
    dpr_leg = creature_export.get('legendary_dpr', 0)
    dpr_total = creature_export.get('total_dpr', 0)
    dpr_base = creature_export.get('dpr_baseline', 0)
    dpr_dev = creature_export.get('dpr_deviation', 0)
    dpr_feat_str = f'{dpr_feat:>+8.0f}'
    if dpr_leg > 0:
        dpr_feat_str = f'{dpr_feat + dpr_leg:>+8.0f}'
    print(f"    {'DPR':<12} {dpr_est:>9.0f}  {dpr_feat_str}  {dpr_total:>7.0f}  {dpr_base:>8.0f}  {dpr_dev:>+9.0f}", end='')
    if dpr_leg > 0:
        print(f"  (feat:{dpr_feat:.0f} + leg:{dpr_leg:.0f})")
    else:
        print()

    # Save DC row
    dc_est = creature_export.get('highest_save_dc', 0)
    dc_base = creature_export.get('dc_baseline', 0)
    dc_dev = creature_export.get('save_dc_deviation', 0)
    print(f"    {'Save DC':<12} {dc_est:>9.0f}  {'--':>8}  {dc_est:>7.0f}  {dc_base:>8.0f}  {dc_dev:>+9.0f}")

    # Costed DMG Features
    details = _get_costed_features_detail(creature_export)

    print(f"\n  Costed DMG Features:")
    for category, label, total_val in [
        ('ac', 'feature_ac', creature_contrib.get('feature_ac', 0)),
        ('attack', 'feature_attack', creature_contrib.get('feature_attack', 0)),
        ('dpr', 'feature_dpr', creature_contrib.get('feature_dpr', 0)),
        ('hp', 'feature_hp', feature_hp),
    ]:
        items = details[category]
        if items:
            item_strs = ', '.join(f'{name} {cost}' for name, cost in items)
            print(f"    {label} ({total_val:>+.0f}):  {item_strs}")
        else:
            print(f"    {label} ({total_val:>+.0f}):  (none)")

    # HP Penalties
    print(f"\n  HP Penalties:")

    for feature in PHASE2_FEATURES:
        feature_value = creature_contrib.get(feature, 0)
        contrib_col = f'phase2_{feature}_contribution'
        hp_impact = creature_contrib.get(contrib_col, 0)

        try:
            val_str = f"{float(feature_value):+.1f}"
        except (ValueError, TypeError):
            val_str = str(feature_value)

        print(f"    {feature:<35} value: {val_str:>6}  hp impact: {hp_impact:>+7.0f}")

    print(f"    {'-'*58}")
    print(f"    Phase 2 Total:                                   {creature_contrib.get('phase2_total_contribution', 0):>+7.0f}")
    print(f"    HP after Phase 2:                              {creature_contrib['hp_after_phase2']:>8.0f}")

    # ── Resistance/Immunity Penalties ─────────────────────────────────────────
    print(f"\nRESISTANCE/IMMUNITY PENALTIES")
    res_penalty = creature_contrib.get('resist_immun_resistance_penalty', 0)
    imm_penalty = creature_contrib.get('resist_immun_immunity_penalty', 0)

    if res_penalty != 0 or imm_penalty != 0:
        print(f"  Resistance Penalty:                              {res_penalty:>8.0f}")
        print(f"  Immunity Penalty:                                {imm_penalty:>8.0f}")
        print(f"  Total Penalty:                                   {creature_contrib.get('resist_immun_total_penalty', 0):>8.0f}")
    else:
        print(f"  No resistances or immunities")
    print(f"  HP after Resist/Immun:                           {creature_contrib['hp_after_resist_immun_penalty']:>8.0f}")

    # ── Phase 3: Individual Features ──────────────────────────────────────────
    print(f"\nPHASE 3: INDIVIDUAL FEATURES")

    phase3_cols = [col for col in contributions_df.columns
                   if col.startswith('phase3_')
                   and col != 'phase3_total_contribution'
                   and col != 'phase3_intercept']

    for col in sorted(phase3_cols):
        feature_name = col.replace('phase3_', '')
        hp_impact = creature_contrib.get(col, 0)

        if feature_name in creature_export.index:
            feature_value = creature_export[feature_name]
        else:
            feature_value = 'N/A'

        try:
            val_str = f"{float(feature_value):.1f}"
        except (ValueError, TypeError):
            val_str = str(feature_value)

        print(f"  Feature: {feature_name:<35} value: {val_str:>6}  hp impact: {hp_impact:>+7.0f}")

    print(f"\n  Intercept:                                       {creature_contrib.get('phase3_intercept', 0):>+8.0f}")
    print(f"  {'-' * 53}")
    print(f"  Phase 3 Total:                                   {creature_contrib.get('phase3_total_contribution', 0):>+8.0f}")

    # ── Final Summary ─────────────────────────────────────────────────────────
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


def analyze_predictions(df_tier, tier_name):
    """Analyze prediction accuracy for a tier."""
    # Create analysis dataframe - start with copy of all columns for highlight support
    analysis = df_tier.copy()

    # Add/rename standard analysis columns
    y_actual = df_tier['actual_hp'].values
    y_pred = df_tier['predicted_hp'].values
    analysis['Actual_HP'] = y_actual
    analysis['Predicted_HP'] = y_pred
    analysis['CR'] = df_tier['cr_numeric'].values
    analysis['Error'] = y_actual - y_pred
    analysis['Abs_Error'] = np.abs(y_actual - y_pred)
    analysis['Pct_Error'] = ((y_actual - y_pred) / y_actual) * 100
    
    # Sort by absolute error
    analysis = analysis.sort_values('Abs_Error')
    
    # Get best and worst 10
    best_10 = analysis.head(10)
    worst_10 = analysis.tail(10)
    
    print(f"\n{tier_name} - Best 10 Predictions:")
    print(best_10[['Name', 'CR', 'Actual_HP', 'Predicted_HP', 'Error']].to_string(index=False))
    
    print(f"\n{tier_name} - Worst 10 Predictions:")
    print(worst_10[['Name', 'CR', 'Actual_HP', 'Predicted_HP', 'Error']].to_string(index=False))
    
    # Summary stats
    print(f"\n{tier_name} Summary:")
    print(f"  Total creatures: {len(analysis)}")
    print(f"  Mean Absolute Error: {analysis['Abs_Error'].mean():.2f} HP")
    print(f"  Median Absolute Error: {analysis['Abs_Error'].median():.2f} HP")
    print(f"  Max Error: {analysis['Abs_Error'].max():.2f} HP")
    print(f"  Mean % Error: {analysis['Pct_Error'].abs().mean():.2f}%")
    
    return analysis

def analyze_predictions_by_cr(df):
    available_tiers = df['cr_tier'].sort_values().unique()
    analysis_dfs = {}
    for tier in available_tiers:
        df_tier = df[df['cr_tier']==tier].reset_index(drop=True)
        analysis_dfs[tier] = analyze_predictions(df_tier, CR_TIERS[tier]['label'])
    return analysis_dfs


# =============================================================================
# Summary Plotting
# =============================================================================

# Helper function for scatter plots
def plot_performance_cr_scatter(ax, analysis, title, highlight_feature=None, is_binary=None, vmin=None, vmax=None):
    scatter = None
    if highlight_feature is None or highlight_feature not in analysis.columns:
        # Default behavior - all blue
        ax.scatter(analysis['Actual_HP'], analysis['Predicted_HP'],
                   alpha=0.6, s=50, color='blue')
    elif is_binary:
        # Binary coloring - blue for 0/False, orange for 1/True
        colors = ['blue' if v in (0, False, 0.0) else 'orange'
                  for v in analysis[highlight_feature]]
        ax.scatter(analysis['Actual_HP'], analysis['Predicted_HP'],
                   alpha=0.6, s=50, c=colors)
    else:
        # Gradient coloring
        scatter = ax.scatter(analysis['Actual_HP'], analysis['Predicted_HP'],
                   alpha=0.6, s=50, c=analysis[highlight_feature],
                   cmap='viridis', vmin=vmin, vmax=vmax)

    max_val = max(analysis['Actual_HP'].max(), analysis['Predicted_HP'].max())
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='Perfect Prediction')
    ax.set_xlabel('Actual HP')
    ax.set_ylabel('Predicted HP')
    ax.set_title(f'{title}\nMAE: {analysis["Abs_Error"].mean():.2f} HP ({len(analysis)} creatures)')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)
    return scatter

def plot_performance_scatter(analysis_dfs, highlight_feature=None):
    # Create visualizations - 5 CR buckets

    print("\n" + "=" * 80)
    print("📊 VISUALIZATION: Actual vs Predicted HP (5 CR Buckets)")
    print("=" * 80)

    # Detect if binary and calculate vmin/vmax for gradient
    is_binary = None
    vmin, vmax = None, None
    if highlight_feature is not None:
        is_binary = _is_binary_feature(analysis_dfs, highlight_feature)
        if not is_binary:
            # Calculate global vmin/vmax for consistent gradient across tiers
            all_vals = []
            for tier_df in analysis_dfs.values():
                if highlight_feature in tier_df.columns:
                    all_vals.extend(tier_df[highlight_feature].dropna().tolist())
            if all_vals:
                vmin, vmax = min(all_vals), max(all_vals)

    # helper for R2
    def _r2(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        if y_true.size == 0:
            return float('nan')
        ss_res = ((y_true - y_pred) ** 2).sum()
        ss_tot = ((y_true - y_true.mean()) ** 2).sum()
        if ss_tot == 0:
            return float('nan')
        return 1 - ss_res / ss_tot

    def _title_with_r2(df, base_title):
        if highlight_feature and (highlight_feature in df.columns):
            mask_true = df[highlight_feature] != 0
            mask_false = df[highlight_feature] == 0
            r2_t = _r2(df.loc[mask_true, 'actual_hp'], df.loc[mask_true, 'predicted_hp']) if mask_true.any() else float('nan')
            r2_f = _r2(df.loc[mask_false, 'actual_hp'], df.loc[mask_false, 'predicted_hp']) if mask_false.any() else float('nan')
            return f"{base_title}\nR2: True {r2_t:.3f} False {r2_f:.3f}"
        return base_title

    analysis_cr1 = analysis_dfs['cr1']
    analysis_cr2 = analysis_dfs['cr2']
    analysis_cr3 = analysis_dfs['cr3']
    analysis_cr4 = analysis_dfs['cr4']
    analysis_cr5 = analysis_dfs['cr5']

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    plot_performance_cr_scatter(axes[0], analysis_cr1, _title_with_r2(analysis_cr1, 'CR < 1'), highlight_feature, is_binary, vmin, vmax)
    plot_performance_cr_scatter(axes[1], analysis_cr2, _title_with_r2(analysis_cr2, 'CR 1-4'), highlight_feature, is_binary, vmin, vmax)
    plot_performance_cr_scatter(axes[2], analysis_cr3, _title_with_r2(analysis_cr3, 'CR 5-10'), highlight_feature, is_binary, vmin, vmax)
    plot_performance_cr_scatter(axes[3], analysis_cr4, _title_with_r2(analysis_cr4, 'CR 11-16'), highlight_feature, is_binary, vmin, vmax)
    scatter = plot_performance_cr_scatter(axes[4], analysis_cr5, _title_with_r2(analysis_cr5, 'CR > 16'), highlight_feature, is_binary, vmin, vmax)

    # Use 6th subplot for legend/colorbar or hide it
    if highlight_feature and not is_binary and scatter is not None:
        # Add colorbar for gradient
        plt.colorbar(scatter, ax=axes[5], label=highlight_feature)
        axes[5].axis('off')
    elif highlight_feature and is_binary:
        # Add legend for binary
        legend_elements = [Patch(facecolor='blue', label=f'{highlight_feature}=0'),
                          Patch(facecolor='orange', label=f'{highlight_feature}=1')]
        axes[5].legend(handles=legend_elements, loc='center', fontsize=12)
        axes[5].axis('off')
    else:
        axes[5].axis('off')

    plt.tight_layout()
    plt.show()


# =============================================================================
# Feature Importance
# =============================================================================

def _compute_dmg_feature_hp_impact(feat_name, tier, creatures_with):
    """Compute per-creature HP impact of a single DMG feature for a given tier.

    Converts the feature's DMG-specified AC/attack/DPR/HP costs into an
    estimated HP impact using Phase 2 penalty rates.

    Returns negative values (features reduce predicted HP).
    """
    penalties = PHASE2_PENALTIES[tier]
    impact = 0.0

    # AC cost → HP via ac_deviation penalty
    ac_key = feat_name.replace('_', ' ')
    if ac_key in DMG_AC_ADJUSTMENTS:
        impact += DMG_AC_ADJUSTMENTS[ac_key] * penalties['ac_deviation']

    # Attack cost → HP via attack_deviation penalty
    if ac_key in DMG_ATTACK_ADJUSTMENTS:
        impact += DMG_ATTACK_ADJUSTMENTS[ac_key] * penalties['attack_deviation']

    # DPR cost → HP via dpr_deviation penalty
    if feat_name in DMG_DPR_ADJUSTMENTS:
        impact += DMG_DPR_ADJUSTMENTS[feat_name] * penalties['dpr_deviation']

    # HP costs → direct HP reduction
    if feat_name in DMG_HP_PER_USE:
        per_use = DMG_HP_PER_USE[feat_name].get(tier, 0)
        impact -= per_use * 3  # standard 3 uses

    if feat_name in DMG_HP_BY_TIER:
        impact -= DMG_HP_BY_TIER[feat_name].get(tier, 0)

    if feat_name in DMG_HP_PERCENTAGE:
        pct = DMG_HP_PERCENTAGE[feat_name]
        eligible = creatures_with[creatures_with['cr_numeric'] <= 10]
        if len(eligible) > 0:
            mean_baseline = eligible['hp_baseline'].mean()
            impact -= mean_baseline * pct / (1 + pct) * len(eligible) / len(creatures_with)

    if feat_name in DMG_HP_MULTIPLIER:
        mult = DMG_HP_MULTIPLIER[feat_name]
        mean_baseline = creatures_with['hp_baseline'].mean()
        impact -= mean_baseline * (1 - 1 / mult)

    return impact


def feature_importance_by_tier(contributions_df, export_df=None):
    """
    Show mean HP impact of each modeling feature by CR tier.

    Includes DMG individual feature costs (requires export_df),
    Phase 1 aggregate feature costs, Phase 2 features (with specified
    penalty rates), and Phase 3 features (learned coefficients).

    Args:
        contributions_df: DataFrame with per-creature feature contributions
        export_df: DataFrame with creature features (for DMG feature flags)

    Returns:
        DataFrame with mean HP impact per feature per tier
    """
    df = contributions_df.copy()
    df['cr_tier'] = df['CR'].apply(get_cr_tier)

    tiers = ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']
    tier_labels = {t: CR_TIERS[t]['label'] for t in tiers}

    # Identify contribution columns
    phase1_features = ['feature_hp', 'feature_ac', 'feature_attack', 'feature_dpr']
    phase2_cols = {f'phase2_{f}_contribution': f for f in PHASE2_FEATURES}
    phase3_cols = {c: c.replace('phase3_', '') for c in df.columns
                   if c.startswith('phase3_')
                   and c not in ('phase3_total_contribution', 'phase3_intercept')}

    rows = []

    # ── DMG individual features (requires export_df) ─────────────────────
    if export_df is not None:
        export = export_df.copy()
        export['cr_tier'] = export['cr_numeric'].apply(get_cr_tier)

        # Which features have any DMG-specified cost
        ac_names = {k.replace(' ', '_') for k in DMG_AC_ADJUSTMENTS}
        atk_names = {k.replace(' ', '_') for k in DMG_ATTACK_ADJUSTMENTS}
        dpr_names = set(DMG_DPR_ADJUSTMENTS)
        hp_names = (set(DMG_HP_PER_USE) | set(DMG_HP_BY_TIER)
                    | set(DMG_HP_PERCENTAGE) | set(DMG_HP_MULTIPLIER))
        all_costed = ac_names | atk_names | dpr_names | hp_names

        for feat_name in DMG_FEATURE_NAMES:
            col = f'feature_{feat_name}'
            if col not in export.columns:
                continue

            row = {'phase': 'DMG Features', 'feature': feat_name}
            any_present = False

            for tier in tiers:
                tier_data = export[export['cr_tier'] == tier]
                n_total = len(tier_data)
                if n_total == 0:
                    row[tier] = 0.0
                    row[f'{tier}_count'] = 0
                    continue

                mask = tier_data[col] == 1
                n_with = int(mask.sum())
                row[f'{tier}_count'] = n_with

                if n_with == 0:
                    row[tier] = 0.0
                    continue

                any_present = True
                creatures_with = tier_data[mask]
                row[tier] = _compute_dmg_feature_hp_impact(
                    feat_name, tier, creatures_with)

            if any_present:
                rows.append(row)

    # ── Phase 1: aggregate feature costs ─────────────────────────────────
    for col in phase1_features:
        if col not in df.columns:
            continue
        row = {'phase': 'Phase 1', 'feature': col}
        for tier in tiers:
            tier_df = df[df['cr_tier'] == tier]
            if len(tier_df) > 0:
                # feature_hp is subtracted from baseline, so negate for HP impact
                if col == 'feature_hp':
                    row[tier] = -tier_df[col].mean()
                else:
                    row[tier] = tier_df[col].mean()
            else:
                row[tier] = 0.0
        rows.append(row)

    # ── Phase 2 ──────────────────────────────────────────────────────────
    for col, feature in phase2_cols.items():
        if col not in df.columns:
            continue
        row = {'phase': 'Phase 2', 'feature': feature}
        for tier in tiers:
            row[tier] = PHASE2_PENALTIES.get(tier, {}).get(feature, 0)
        rows.append(row)

    # ── Phase 3 ──────────────────────────────────────────────────────────
    for col, feature in phase3_cols.items():
        if col not in df.columns:
            continue
        row = {'phase': 'Phase 3', 'feature': feature}
        for tier in tiers:
            tier_df = df[df['cr_tier'] == tier]
            tier_vals = tier_df[col] if len(tier_df) > 0 else pd.Series(dtype=float)
            nonzero = tier_vals[tier_vals != 0]
            row[tier] = nonzero.mean() if len(nonzero) > 0 else 0.0
            row[f'{tier}_count'] = len(nonzero)
        rows.append(row)

    result_df = pd.DataFrame(rows)

    # Sort within each phase by absolute mean impact (descending)
    result_df['_abs_mean'] = result_df[tiers].abs().mean(axis=1)
    result_df = result_df.sort_values(['phase', '_abs_mean'], ascending=[True, False])
    result_df = result_df.drop('_abs_mean', axis=1).reset_index(drop=True)

    # ── Display ──────────────────────────────────────────────────────────
    col_w = 10  # width per tier column
    header_w = 35 + (col_w + 1) * len(tiers)

    def _print_section_header(title):
        print(f"\n  {title}")
        print(f"  {'Feature':<35}", end='')
        for tier in tiers:
            print(f" {tier_labels[tier]:>{col_w}}", end='')
        print()
        print(f"  {'-' * header_w}")

    print("=" * 90)
    print("FEATURE IMPORTANCE BY CR TIER")
    print("=" * 90)

    # DMG individual features (per-creature HP impact + count)
    dmg = result_df[result_df['phase'] == 'DMG Features']
    if len(dmg) > 0:
        _print_section_header("DMG INDIVIDUAL FEATURE COSTS (per-creature HP impact)")
        for _, row in dmg.iterrows():
            print(f"  {row['feature']:<35}", end='')
            for tier in tiers:
                val = row[tier]
                if val != 0:
                    print(f" {val:>{col_w}.1f}", end='')
                else:
                    print(f" {'--':>{col_w}}", end='')
            print()
            print(f"    {'(creature count)':<33}", end='')
            for tier in tiers:
                count = int(row.get(f'{tier}_count', 0))
                if count > 0:
                    print(f" {count:>{col_w}}", end='')
                else:
                    print(f" {'--':>{col_w}}", end='')
            print()

    # Phase 1: aggregate feature costs
    _print_section_header("PHASE 1: AGGREGATE DMG FEATURE COSTS (mean across tier)")
    p1 = result_df[result_df['phase'] == 'Phase 1']
    for _, row in p1.iterrows():
        label = row['feature']
        if label == 'feature_hp':
            label += '  (HP impact)'
        else:
            label += '  (stat adj.)'
        print(f"  {label:<35}", end='')
        for tier in tiers:
            print(f" {row[tier]:>{col_w}.1f}", end='')
        print()

    # Phase 2
    _print_section_header("PHASE 2: SPECIFIED PENALTIES (cost per unit)")
    p2 = result_df[result_df['phase'] == 'Phase 2']
    for _, row in p2.iterrows():
        print(f"  {row['feature']:<35}", end='')
        for tier in tiers:
            val = row[tier]
            if val != 0:
                print(f" {val:>{col_w}.2f}", end='')
            else:
                print(f" {'--':>{col_w}}", end='')
        print()

    # Phase 3
    _print_section_header("PHASE 3: LEARNED COEFFICIENTS (mean among creatures with feature)")
    p3 = result_df[result_df['phase'] == 'Phase 3']
    for _, row in p3.iterrows():
        print(f"  {row['feature']:<35}", end='')
        for tier in tiers:
            val = row[tier]
            if val != 0:
                print(f" {val:>{col_w}.1f}", end='')
            else:
                print(f" {'--':>{col_w}}", end='')
        print()
        print(f"    {'(creature count)':<33}", end='')
        for tier in tiers:
            count = int(row.get(f'{tier}_count', 0))
            if count > 0:
                print(f" {count:>{col_w}}", end='')
            else:
                print(f" {'--':>{col_w}}", end='')
        print()

    # Clean return DataFrame: drop internal columns, rename tiers to labels
    drop_cols = [f'{t}_penalty' for t in tiers] + [f'{t}_count' for t in tiers]
    return_df = result_df.drop(columns=drop_cols, errors='ignore')
    return_df = return_df.rename(columns={t: tier_labels[t] for t in tiers})

    return return_df


# Helper function for error histograms
def plot_error_cr_hist(ax, analysis, title):
    ax.hist(analysis['Error'], bins=20, alpha=0.7, 
            color='steelblue', edgecolor='black')
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Error')
    ax.axvline(x=analysis['Error'].median(), color='green', linestyle='-', linewidth=2, label=f'Median: {analysis["Error"].median():.1f}')
    ax.set_xlabel('Error (Actual - Predicted)')
    ax.set_ylabel('Frequency')
    ax.set_title(f'{title}\n({len(analysis)} creatures)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)


def plot_error_hist(analysis_dfs):
    # Error distribution plots - 5 CR buckets
    print("\n" + "=" * 80)
    print("📊 VISUALIZATION: Error Distribution (5 CR Buckets)")
    print("=" * 80)
    
    analysis_cr1 = analysis_dfs['cr1']
    analysis_cr2 = analysis_dfs['cr2']
    analysis_cr3 = analysis_dfs['cr3']
    analysis_cr4 = analysis_dfs['cr4']
    analysis_cr5 = analysis_dfs['cr5']

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()    

    plot_error_cr_hist(axes[0], analysis_cr1, 'CR < 1')
    plot_error_cr_hist(axes[1], analysis_cr2, 'CR 1-4')
    plot_error_cr_hist(axes[2], analysis_cr3, 'CR 5-10')
    plot_error_cr_hist(axes[3], analysis_cr4, 'CR 11-16')
    plot_error_cr_hist(axes[4], analysis_cr5, 'CR > 16')

    # Hide the 6th subplot (empty)
    axes[5].axis('off')

    plt.tight_layout()
    plt.show()