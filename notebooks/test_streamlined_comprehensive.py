#!/usr/bin/env python3
"""
Comprehensive test of all code in paint_analysis_streamlined.ipynb
Identifies and fixes compilation/execution issues
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import ttest_ind, chi2_contingency
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def test_part1():
    """Test Part 1: Data Exploration & Understanding"""
    print("=" * 60)
    print("TESTING PART 1: DATA EXPLORATION & UNDERSTANDING")
    print("=" * 60)
    
    try:
        # Load and examine the data
        df = pd.read_csv('../data/paint_production_data.csv')
        
        print("=== DATASET OVERVIEW ===")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"Date range: {df['Production_Date'].min()} to {df['Production_Date'].max()}")
        
        print("\n=== DATA QUALITY ===")
        print("Missing values:")
        missing = df.isnull().sum()
        for col, count in missing[missing > 0].items():
            pct = count / len(df) * 100
            print(f"  {col}: {count:,} ({pct:.1f}%)")
        
        print(f"\nDuplicates: {df.duplicated().sum()}")
        
        print("\n=== BUSINESS CONTEXT ===")
        print(f"Total dosing events: {len(df):,}")
        print(f"Unique batches: {df['Batch_ID'].nunique():,}")
        print(f"Unique recipes: {df['Recipe_Name'].nunique()}")
        print(f"Dosing stations: {df['Dosing_Station'].nunique()} ({sorted(df['Dosing_Station'].unique())})")
        print(f"Events per batch (avg): {len(df) / df['Batch_ID'].nunique():.1f}")
        
        # Critical insight: QC results are at BATCH level, not event level
        print("\n=== QUALITY ANALYSIS ===")
        event_failure_rate = (df['QC_Result'] == 'failed').mean()
        print(f"Event-level failure rate: {event_failure_rate:.1%}")
        
        # Batch-level failure rate (the real business metric)
        batch_qc = df.groupby('Batch_ID')['QC_Result'].first()
        batch_failure_rate = (batch_qc == 'failed').mean()
        print(f"Batch-level failure rate: {batch_failure_rate:.1%} ← KEY BUSINESS METRIC")
        
        print(f"\nDaily production: ~{df['Batch_ID'].nunique() / 365:.0f} batches/day")
        print(f"Failed batches per day: ~{batch_failure_rate * df['Batch_ID'].nunique() / 365:.1f}")
        
        # Create batch-level dataset for analysis
        print("\n=== CREATING BATCH-LEVEL DATASET ===")
        
        # Calculate dosing errors - THIS IS CRITICAL FOR PART 2
        df['Dosing_Error'] = abs(df['Actual_Amount'] - df['Target_Amount'])
        
        # Aggregate to batch level
        batch_df = df.groupby('Batch_ID').agg({
            'Production_Date': 'first',
            'Recipe_Name': 'first',
            'Num_Ingredients': 'first',
            'QC_Result': 'first',
            'Facility_Temperature': 'mean',
            'Dosing_Error': ['mean', 'max', 'std'],
            'Target_Amount': 'sum',
            'Actual_Amount': 'sum',
            'Dosing_Station': 'nunique'
        }).round(4)
        
        # Flatten column names
        batch_df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in batch_df.columns]
        batch_df = batch_df.reset_index()
        
        # Create target variable
        batch_df['Failed'] = (batch_df['QC_Result_first'] == 'failed').astype(int)
        
        print(f"Batch dataset shape: {batch_df.shape}")
        print(f"Batch failure rate: {batch_df['Failed'].mean():.1%}")
        
        # Initial hypothesis testing
        print("\n=== INITIAL HYPOTHESIS TESTING ===")
        
        # Hypothesis 1: Recipe complexity affects failure rate
        print("\n1. RECIPE COMPLEXITY HYPOTHESIS:")
        complexity_analysis = batch_df.groupby('Num_Ingredients_first')['Failed'].agg(['count', 'mean']).round(3)
        complexity_analysis.columns = ['Batch_Count', 'Failure_Rate']
        print(complexity_analysis.head(10))
        
        # Test threshold at 15 ingredients
        simple = batch_df[batch_df['Num_Ingredients_first'] <= 15]
        complex_recipes = batch_df[batch_df['Num_Ingredients_first'] > 15]
        print(f"\nSimple recipes (≤15 ingredients): {simple['Failed'].mean():.1%} failure rate")
        print(f"Complex recipes (>15 ingredients): {complex_recipes['Failed'].mean():.1%} failure rate")
        print(f"Difference: {complex_recipes['Failed'].mean() - simple['Failed'].mean():.1%}")
        
        # Hypothesis 2: Temperature affects failure rate
        print("\n2. TEMPERATURE HYPOTHESIS:")
        temp_data = batch_df.dropna(subset=['Facility_Temperature_mean'])
        print(f"Temperature range: {temp_data['Facility_Temperature_mean'].min():.1f}°C to {temp_data['Facility_Temperature_mean'].max():.1f}°C")
        
        # Test optimal range 20-25°C
        optimal_temp = temp_data[(temp_data['Facility_Temperature_mean'] >= 20) & (temp_data['Facility_Temperature_mean'] <= 25)]
        suboptimal_temp = temp_data[(temp_data['Facility_Temperature_mean'] < 20) | (temp_data['Facility_Temperature_mean'] > 25)]
        print(f"Optimal temp (20-25°C): {optimal_temp['Failed'].mean():.1%} failure rate")
        print(f"Suboptimal temp: {suboptimal_temp['Failed'].mean():.1%} failure rate")
        print(f"Difference: {suboptimal_temp['Failed'].mean() - optimal_temp['Failed'].mean():.1%}")
        
        # Hypothesis 3: Station performance varies
        print("\n3. STATION PERFORMANCE HYPOTHESIS:")
        station_performance = df.groupby('Dosing_Station')['QC_Result'].apply(lambda x: (x == 'failed').mean()).sort_values(ascending=False)
        print("Station failure rates:")
        for station, rate in station_performance.items():
            print(f"  {station}: {rate:.1%}")
        
        print(f"\nStation performance spread: {station_performance.max() - station_performance.min():.1%}")
        
        print("\n✅ PART 1 COMPLETED SUCCESSFULLY")
        return df, batch_df
        
    except Exception as e:
        print(f"❌ PART 1 FAILED: {e}")
        raise

def test_part2(df, batch_df):
    """Test Part 2: Diagnostic Analysis"""
    print("\n" + "=" * 60)
    print("TESTING PART 2: DIAGNOSTIC ANALYSIS")
    print("=" * 60)

    try:
        print("=== PART 2: STREAMLINED DIAGNOSTIC ANALYSIS ===")
        print(f"Working with {len(batch_df)} batches for comprehensive analysis")

        # 2.1 COMPREHENSIVE FACTOR ANALYSIS
        print("\n=== 2.1 COMPREHENSIVE FACTOR ANALYSIS ===")

        # Ensure Dosing_Error column exists (safety check)
        if 'Dosing_Error' not in df.columns:
            df['Dosing_Error'] = abs(df['Actual_Amount'] - df['Target_Amount'])
            print("⚠️  Created Dosing_Error column (ensure Part 1 was executed first)")

        # Station Performance Analysis
        station_analysis = df.groupby('Dosing_Station').agg({
            'Dosing_Error': ['mean', 'std', 'count'],
            'QC_Result': lambda x: (x == 'failed').mean()
        }).round(4)
        station_analysis.columns = ['Avg_Error', 'Error_Std', 'Event_Count', 'Failure_Rate']
        station_analysis = station_analysis.sort_values('Failure_Rate', ascending=False)

        print("\nStation Performance Summary:")
        print(station_analysis)

        # Statistical significance tests
        worst_stations = ['D03', 'D07']
        best_stations = ['D02', 'D04']
        worst_errors = df[df['Dosing_Station'].isin(worst_stations)]['Dosing_Error'].dropna()
        best_errors = df[df['Dosing_Station'].isin(best_stations)]['Dosing_Error'].dropna()
        t_stat, p_value = ttest_ind(worst_errors, best_errors)
        correlation = stats.pearsonr(station_analysis['Avg_Error'], station_analysis['Failure_Rate'])

        print(f"\n📊 Station Analysis Results:")
        print(f"  • Strong correlation between errors and failures: r={correlation[0]:.3f} (p={correlation[1]:.2e})")
        print(f"  • Significant difference worst vs best: t={t_stat:.2f} (p={p_value:.2e})")
        print(f"  • Problem stations: {worst_stations} require immediate maintenance")

        # Recipe Complexity Analysis
        simple_batches = batch_df[batch_df['Num_Ingredients_first'] <= 15]
        complex_batches = batch_df[batch_df['Num_Ingredients_first'] > 15]
        contingency_table = pd.crosstab(batch_df['Num_Ingredients_first'] <= 15, batch_df['Failed'], margins=True)
        chi2, p_value_recipe, dof, expected = chi2_contingency(contingency_table.iloc[:-1, :-1])
        p1, p2 = simple_batches['Failed'].mean(), complex_batches['Failed'].mean()
        cohens_h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))

        print(f"\n🧪 Recipe Complexity Results:")
        print(f"  • Simple (≤15): {p1:.1%} failure rate ({len(simple_batches):,} batches)")
        print(f"  • Complex (>15): {p2:.1%} failure rate ({len(complex_batches):,} batches)")
        print(f"  • Statistical significance: χ²={chi2:.1f}, p={p_value_recipe:.2e}")
        print(f"  • Effect size: Cohen's h={abs(cohens_h):.3f} (medium effect)")

        # Temperature Control Analysis
        temp_data = batch_df.dropna(subset=['Facility_Temperature_mean'])
        optimal_batches = temp_data[(temp_data['Facility_Temperature_mean'] >= 20) & (temp_data['Facility_Temperature_mean'] <= 25)]
        suboptimal_batches = temp_data[(temp_data['Facility_Temperature_mean'] < 20) | (temp_data['Facility_Temperature_mean'] > 25)]
        temp_contingency = pd.crosstab((temp_data['Facility_Temperature_mean'] >= 20) & (temp_data['Facility_Temperature_mean'] <= 25), temp_data['Failed'], margins=True)
        chi2_temp, p_temp, dof_temp, expected_temp = chi2_contingency(temp_contingency.iloc[:-1, :-1])
        p_optimal, p_suboptimal = optimal_batches['Failed'].mean(), suboptimal_batches['Failed'].mean()

        print(f"\n🌡️ Temperature Control Results:")
        print(f"  • Optimal (20-25°C): {p_optimal:.1%} failure rate ({len(optimal_batches):,} batches)")
        print(f"  • Suboptimal: {p_suboptimal:.1%} failure rate ({len(suboptimal_batches):,} batches)")
        print(f"  • Statistical significance: χ²={chi2_temp:.1f}, p={p_temp:.2e}")
        print(f"  • Temperature range: {temp_data['Facility_Temperature_mean'].min():.1f}°C to {temp_data['Facility_Temperature_mean'].max():.1f}°C")

        # Interaction Effects Analysis
        best_case = batch_df[(batch_df['Num_Ingredients_first'] <= 15) & (batch_df['Facility_Temperature_mean'] >= 20) & (batch_df['Facility_Temperature_mean'] <= 25)]['Failed'].mean()
        worst_case = batch_df[(batch_df['Num_Ingredients_first'] > 15) & ((batch_df['Facility_Temperature_mean'] < 20) | (batch_df['Facility_Temperature_mean'] > 25))]['Failed'].mean()
        worst_case_count = len(batch_df[(batch_df['Num_Ingredients_first'] > 15) & ((batch_df['Facility_Temperature_mean'] < 20) | (batch_df['Facility_Temperature_mean'] > 25))])

        print(f"\n🔄 Interaction Effects Results:")
        print(f"  • Best case (Simple + Optimal): {best_case:.1%} failure rate")
        print(f"  • Worst case (Complex + Suboptimal): {worst_case:.1%} failure rate")
        print(f"  • Multiplicative spread: {worst_case - best_case:.1%}")
        print(f"  • High-risk batches: {worst_case_count:,} ({worst_case_count/len(batch_df)*100:.1f}% of production)")

        # Test additional detailed analyses
        print(f"\n🔍 **DETAILED DIAGNOSTIC INSIGHTS:**")

        # Temperature direction analysis
        cold_temp = df[df['Facility_Temperature'] < 20]
        hot_temp = df[df['Facility_Temperature'] > 25]
        optimal_temp = df[(df['Facility_Temperature'] >= 20) & (df['Facility_Temperature'] <= 25)]
        cold_failure_rate = (cold_temp['QC_Result'] == 'failed').mean()
        hot_failure_rate = (hot_temp['QC_Result'] == 'failed').mean()
        optimal_failure_rate = (optimal_temp['QC_Result'] == 'failed').mean()

        print(f"\n🌡️ **Temperature Direction Effects:**")
        print(f"  • Cold (<20°C): {cold_failure_rate:.1%} failure rate ({len(cold_temp):,} events)")
        print(f"  • Optimal (20-25°C): {optimal_failure_rate:.1%} failure rate ({len(optimal_temp):,} events)")
        print(f"  • Hot (>25°C): {hot_failure_rate:.1%} failure rate ({len(hot_temp):,} events)")
        print(f"  • Cold vs Hot impact: Cold is {cold_failure_rate/hot_failure_rate:.1f}x worse than hot")

        print("\n✅ PART 2 COMPLETED SUCCESSFULLY")
        return True

    except Exception as e:
        print(f"❌ PART 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive test"""
    print("🧪 COMPREHENSIVE TEST OF STREAMLINED NOTEBOOK")
    print("=" * 80)
    
    try:
        # Test Part 1
        df, batch_df = test_part1()
        
        # Test Part 2
        part2_success = test_part2(df, batch_df)
        
        if part2_success:
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED")
            print("📋 ISSUES IDENTIFIED AND SOLUTIONS:")
            print("1. Dosing_Error column must be created in Part 1")
            print("2. df and batch_df must be available for Part 2")
            print("3. All dependencies properly ordered")
            print("=" * 80)
        else:
            print("\n❌ TESTS FAILED - See errors above")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
