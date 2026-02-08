"""
Adanced analysis and investigation utilies for model performances

"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from .feature_config import CR_TIERS, PHASE2_FEATURES
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

    # Phase 2: Combat Stats (now applied BEFORE resistance/immunity)
    print(f"\nPHASE 2: COMBAT STATS")

    # Map feature names to contribution column names
    phase2_contrib_map = {
        'ac_deviation': 'phase2_ac_contribution',
        'attack_deviation': 'phase2_attack_contribution',
        'dpr_deviation': 'phase2_dpr_contribution',
        'save_dc_deviation': 'phase2_save_dc_contribution',
        'has_flying': 'phase2_flying_contribution',
        'has_advantage_condition': 'phase2_advantage_contribution',
        'has_disadvantage_condition': 'phase2_disadvantage_contribution',
        'has_attackers_advantage': 'phase2_attackers_advantage_contribution',
        'inflicts_prone': 'phase2_prone_contribution',
    }

    for feature in PHASE2_FEATURES:
        # Get raw feature value
        feature_value = creature_contrib.get(feature, 0)

        # Get HP contribution
        contrib_col = phase2_contrib_map.get(feature, f'phase2_{feature}_contribution')
        hp_impact = creature_contrib.get(contrib_col, 0)

        try:
            val_str = f"{float(feature_value):.1f}"
        except:
            val_str = str(feature_value)

        print(f"  Feature: {feature:<30} value: {val_str:>6}  hp impact: {hp_impact:>6.0f}")

    print(f"  {'-' * 53}")
    print(f"  Phase 2 Total:                                   {creature_contrib.get('phase2_total_contribution', 0):>8.0f}")
    print(f"  HP after Phase 2:                                {creature_contrib['hp_after_phase2']:>8.0f}")

    # Resistance/Immunity Penalties (now applied AFTER Phase 2)
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

    # Phase 3: Individual Features
    print(f"\nPHASE 3: INDIVIDUAL FEATURES")

    # Get all phase3 columns
    phase3_cols = [col for col in contributions_df.columns
                   if col.startswith('phase3_')
                   and col != 'phase3_total_contribution'
                   and col != 'phase3_intercept']

    for col in sorted(phase3_cols):
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
        if is_binary and highlight_feature and (highlight_feature in df.columns):
            mask_true = df[highlight_feature] == 1
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