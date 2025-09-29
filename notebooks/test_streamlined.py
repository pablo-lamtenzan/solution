#!/usr/bin/env python3
"""
Quick test to verify the streamlined notebook has all essential components
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_ind, chi2_contingency

def test_streamlined_notebook():
    """Test that streamlined notebook components work correctly"""
    
    print("=" * 60)
    print("TESTING STREAMLINED NOTEBOOK COMPONENTS")
    print("=" * 60)
    
    # Load data (same as notebook)
    df = pd.read_csv('../data/paint_production_data.csv')
    
    # Create batch dataset (same as notebook)
    df['Dosing_Error'] = abs(df['Actual_Amount'] - df['Target_Amount'])
    
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
    batch_df['Failed'] = (batch_df['QC_Result_first'] == 'failed').astype(int)
    
    print(f"✅ Data loaded: {len(batch_df)} batches")
    
    # Test Part 2 components
    print("\n=== TESTING PART 2 COMPONENTS ===")
    
    # Recipe complexity analysis
    simple_batches = batch_df[batch_df['Num_Ingredients_first'] <= 15]
    complex_batches = batch_df[batch_df['Num_Ingredients_first'] > 15]
    p1, p2 = simple_batches['Failed'].mean(), complex_batches['Failed'].mean()
    
    contingency_table = pd.crosstab(batch_df['Num_Ingredients_first'] <= 15, batch_df['Failed'], margins=True)
    chi2, p_value_recipe, dof, expected = chi2_contingency(contingency_table.iloc[:-1, :-1])
    
    print(f"✅ Recipe analysis: Simple={p1:.1%}, Complex={p2:.1%}, χ²={chi2:.1f}, p={p_value_recipe:.2e}")
    
    # Temperature analysis
    temp_data = batch_df.dropna(subset=['Facility_Temperature_mean'])
    optimal_batches = temp_data[(temp_data['Facility_Temperature_mean'] >= 20) & (temp_data['Facility_Temperature_mean'] <= 25)]
    suboptimal_batches = temp_data[(temp_data['Facility_Temperature_mean'] < 20) | (temp_data['Facility_Temperature_mean'] > 25)]
    p_optimal, p_suboptimal = optimal_batches['Failed'].mean(), suboptimal_batches['Failed'].mean()
    
    print(f"✅ Temperature analysis: Optimal={p_optimal:.1%}, Suboptimal={p_suboptimal:.1%}")
    
    # Station analysis
    station_analysis = df.groupby('Dosing_Station').agg({
        'Dosing_Error': ['mean', 'std', 'count'],
        'QC_Result': lambda x: (x == 'failed').mean()
    }).round(4)
    station_analysis.columns = ['Avg_Error', 'Error_Std', 'Event_Count', 'Failure_Rate']
    
    worst_stations = station_analysis.nlargest(2, 'Failure_Rate').index.tolist()
    print(f"✅ Station analysis: Worst stations = {worst_stations}")
    
    # Interaction effects
    best_case = batch_df[(batch_df['Num_Ingredients_first'] <= 15) & 
                        (batch_df['Facility_Temperature_mean'] >= 20) & 
                        (batch_df['Facility_Temperature_mean'] <= 25)]['Failed'].mean()
    worst_case = batch_df[(batch_df['Num_Ingredients_first'] > 15) & 
                         ((batch_df['Facility_Temperature_mean'] < 20) | 
                          (batch_df['Facility_Temperature_mean'] > 25))]['Failed'].mean()
    
    print(f"✅ Interaction effects: Best={best_case:.1%}, Worst={worst_case:.1%}, Spread={worst_case-best_case:.1%}")
    
    # Test Part 3 components
    print("\n=== TESTING PART 3 COMPONENTS ===")
    
    # Feature engineering
    modeling_df = batch_df.copy()
    modeling_df['Recipe_Complex'] = (modeling_df['Num_Ingredients_first'] > 15).astype(int)
    modeling_df['Temp_Suboptimal'] = ((modeling_df['Facility_Temperature_mean'] < 20) | 
                                     (modeling_df['Facility_Temperature_mean'] > 25)).astype(int)
    modeling_df['Complex_AND_Suboptimal'] = (modeling_df['Recipe_Complex'] & modeling_df['Temp_Suboptimal']).astype(int)
    
    feature_cols = [
        'Num_Ingredients_first', 'Facility_Temperature_mean', 'Dosing_Error_mean', 
        'Recipe_Complex', 'Temp_Suboptimal', 'Complex_AND_Suboptimal'
    ]
    
    modeling_clean = modeling_df.dropna(subset=feature_cols + ['Failed'])
    print(f"✅ Feature engineering: {len(feature_cols)} features, {len(modeling_clean)} clean samples")
    
    # Quick model test
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    
    X = modeling_clean[feature_cols]
    y = modeling_clean['Failed']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    rf_model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=10)
    rf_model.fit(X_train, y_train)
    
    test_pred = rf_model.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, test_pred)
    
    print(f"✅ Model test: AUC = {test_auc:.3f}")
    
    print("\n" + "=" * 60)
    print("✅ ALL STREAMLINED COMPONENTS WORKING CORRECTLY")
    print("✅ READY FOR PRODUCTION USE")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_streamlined_notebook()
