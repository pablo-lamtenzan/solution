#!/usr/bin/env python3
"""
Test script for Part 1 of Paint Quality Analysis
Executes all Part 1 code from the notebook to ensure it works correctly
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('default')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)

print("✓ Libraries imported successfully")

def test_part1():
    """Test all Part 1 functionality"""
    
    print("\n" + "="*50)
    print("TESTING PART 1: DATA EXPLORATION & UNDERSTANDING")
    print("="*50)
    
    # Load and examine the data
    df = pd.read_csv('../data/paint_production_data.csv')
    
    print("\n=== DATASET OVERVIEW ===")
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
    
    # Calculate dosing errors
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

    # Create target variable (QC_Result becomes QC_Result_first after flattening)
    batch_df['Failed'] = (batch_df['QC_Result_first'] == 'failed').astype(int)
    
    print(f"Batch dataset shape: {batch_df.shape}")
    print(f"Batch failure rate: {batch_df['Failed'].mean():.1%}")
    print("Batch dataset ready for analysis")
    
    # Initial hypothesis testing
    print("\n=== INITIAL HYPOTHESIS TESTING ===")
    
    # Hypothesis 1: Recipe complexity affects failure rate
    print("\n1. RECIPE COMPLEXITY HYPOTHESIS:")
    complexity_analysis = batch_df.groupby('Num_Ingredients_first')['Failed'].agg(['count', 'mean']).round(3)
    complexity_analysis.columns = ['Batch_Count', 'Failure_Rate']
    print("Top 10 complexity levels:")
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
    
    # Summary
    print("\n" + "="*50)
    print("PART 1 SUMMARY")
    print("="*50)
    print("Key Findings:")
    print(f"- Batch failure rate: {batch_df['Failed'].mean():.1%} (the critical business metric)")
    print(f"- Recipe complexity effect: Simple (≤15 ingredients) = {simple['Failed'].mean():.1%} vs Complex (>15) = {complex_recipes['Failed'].mean():.1%}")
    print(f"- Temperature effect: Optimal (20-25°C) = {optimal_temp['Failed'].mean():.1%} vs Suboptimal = {suboptimal_temp['Failed'].mean():.1%}")
    print(f"- Station variation: Performance spread of {station_performance.max() - station_performance.min():.1%} between best and worst stations")
    
    print("\nHypotheses for Part 2:")
    print("1. Recipe complexity >15 ingredients significantly increases failure risk")
    print("2. Temperature outside 20-25°C range increases failure risk")
    print("3. Certain dosing stations have systematic performance issues")
    print("4. Multiple factors may interact (multiplicative effects)")
    
    print(f"\nData Quality: Manageable missing values ({df.isnull().sum().sum():,} total), realistic industrial dataset")
    
    print("\n✅ PART 1 STATUS: COMPLETE")
    print("✅ All code executed successfully")
    print("✅ Ready for Part 2: Diagnostic Analysis")
    
    return df, batch_df

if __name__ == "__main__":
    df, batch_df = test_part1()
    print(f"\n🎯 Final verification:")
    print(f"   Original dataset: {df.shape}")
    print(f"   Batch dataset: {batch_df.shape}")
    print(f"   Batch failure rate: {batch_df['Failed'].mean():.1%}")
    print(f"   All systems ready for Part 2!")
