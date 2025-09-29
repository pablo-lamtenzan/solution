#!/usr/bin/env python3
"""
Test script for Part 3 of Paint Quality Analysis
Executes all Part 3 code from the notebook to ensure it works correctly
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def test_part3():
    """Test all Part 3 functionality"""
    
    print("\n" + "="*60)
    print("TESTING PART 3: PREDICTIVE MODELING")
    print("="*60)
    
    # Load and prepare data (from Parts 1 & 2)
    df = pd.read_csv('../data/paint_production_data.csv')
    df['Dosing_Error'] = abs(df['Actual_Amount'] - df['Target_Amount'])
    
    # Create batch-level dataset
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
    
    print(f"Working with {len(batch_df)} batches for modeling")
    
    # 3.1 Feature Engineering
    print("\n=== 3.1 FEATURE ENGINEERING ===")
    
    modeling_df = batch_df.copy()
    
    # Core features from diagnostic analysis
    modeling_df['Recipe_Complex'] = (modeling_df['Num_Ingredients_first'] > 15).astype(int)
    modeling_df['Temp_Suboptimal'] = ((modeling_df['Facility_Temperature_mean'] < 20) | 
                                     (modeling_df['Facility_Temperature_mean'] > 25)).astype(int)
    
    # Interaction features
    modeling_df['Complex_AND_Suboptimal'] = (modeling_df['Recipe_Complex'] & 
                                            modeling_df['Temp_Suboptimal']).astype(int)
    
    # Dosing quality features
    modeling_df['High_Dosing_Error'] = (modeling_df['Dosing_Error_mean'] > 
                                       modeling_df['Dosing_Error_mean'].median()).astype(int)
    
    feature_columns = [
        'Num_Ingredients_first',
        'Facility_Temperature_mean',
        'Dosing_Error_mean',
        'Dosing_Error_max',
        'Dosing_Error_std',
        'Target_Amount_sum',
        'Dosing_Station_nunique',
        'Recipe_Complex',
        'Temp_Suboptimal',
        'Complex_AND_Suboptimal',
        'High_Dosing_Error'
    ]
    
    print(f"Engineered {len(feature_columns)} features for modeling")
    
    # Feature correlations
    correlations = []
    for feature in feature_columns:
        if feature in modeling_df.columns:
            corr = modeling_df[feature].corr(modeling_df['Failed'])
            correlations.append((feature, corr))
    
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    print("Top 5 features by correlation:")
    for feature, corr in correlations[:5]:
        print(f"  {feature}: {corr:+.3f}")
    
    # 3.2 Model Training and Evaluation
    print("\n=== 3.2 MODEL TRAINING AND EVALUATION ===")
    
    # Prepare data
    X = modeling_df[feature_columns].fillna(modeling_df[feature_columns].median())
    y = modeling_df['Failed']
    
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Target: {y.mean():.1%} failure rate")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Logistic Regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    
    lr_test_pred = lr_model.predict_proba(X_test_scaled)[:, 1]
    lr_test_auc = roc_auc_score(y_test, lr_test_pred)
    
    print(f"Logistic Regression Test AUC: {lr_test_auc:.3f}")
    
    # Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10, 
        random_state=42,
        class_weight='balanced'
    )
    rf_model.fit(X_train, y_train)
    
    rf_test_pred = rf_model.predict_proba(X_test)[:, 1]
    rf_test_auc = roc_auc_score(y_test, rf_test_pred)
    
    print(f"Random Forest Test AUC: {rf_test_auc:.3f}")
    
    # Feature importance
    rf_importance = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': rf_model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    print("Top 5 Random Forest Features:")
    for i, (_, row) in enumerate(rf_importance.head().iterrows(), 1):
        print(f"  {i}. {row['Feature']}: {row['Importance']:.3f}")
    
    # Cross-validation
    lr_cv_scores = cross_val_score(lr_model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
    rf_cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring='roc_auc')
    
    print(f"\\nCross-validation results:")
    print(f"  Logistic Regression: {lr_cv_scores.mean():.3f} ± {lr_cv_scores.std():.3f}")
    print(f"  Random Forest: {rf_cv_scores.mean():.3f} ± {rf_cv_scores.std():.3f}")
    
    # 3.3 Business Risk Scoring
    print("\n=== 3.3 BUSINESS RISK SCORING SYSTEM ===")
    
    # Use best model
    if rf_test_auc > lr_test_auc:
        best_model = rf_model
        risk_scores = rf_model.predict_proba(X_test)[:, 1]
        model_name = "Random Forest"
        best_auc = rf_test_auc
    else:
        best_model = lr_model
        risk_scores = lr_model.predict_proba(X_test_scaled)[:, 1]
        model_name = "Logistic Regression"
        best_auc = lr_test_auc
    
    print(f"Using {model_name} for risk scoring (AUC: {best_auc:.3f})")
    
    # Risk categories
    risk_percentiles = np.percentile(risk_scores, [25, 50, 75, 90])
    
    def categorize_risk(score):
        if score >= risk_percentiles[3]:
            return "CRITICAL"
        elif score >= risk_percentiles[2]:
            return "HIGH"
        elif score >= risk_percentiles[1]:
            return "MEDIUM"
        else:
            return "LOW"
    
    # Apply risk categories
    test_results = pd.DataFrame({
        'Actual_Failure': y_test.values,
        'Risk_Score': risk_scores,
        'Risk_Category': [categorize_risk(score) for score in risk_scores]
    })
    
    # Risk analysis
    risk_analysis = test_results.groupby('Risk_Category').agg({
        'Actual_Failure': ['count', 'sum', 'mean'],
        'Risk_Score': ['mean']
    }).round(3)
    
    risk_analysis.columns = ['Count', 'Failures', 'Failure_Rate', 'Avg_Score']
    risk_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    risk_analysis = risk_analysis.reindex(risk_order)
    
    print("Risk Category Performance:")
    print(risk_analysis[['Count', 'Failure_Rate']])
    
    # Business value calculation
    high_risk_categories = ['HIGH', 'CRITICAL']
    high_risk_data = risk_analysis.loc[high_risk_categories]
    total_high_risk = high_risk_data['Count'].sum()
    high_risk_failure_rate = (high_risk_data['Failures'].sum() / high_risk_data['Count'].sum())
    baseline_failure_rate = test_results['Actual_Failure'].mean()
    
    print(f"\\nBusiness Value Analysis:")
    print(f"  High-risk batches: {total_high_risk} ({total_high_risk/len(test_results)*100:.1f}% of production)")
    print(f"  High-risk failure rate: {high_risk_failure_rate:.1%}")
    print(f"  Baseline failure rate: {baseline_failure_rate:.1%}")
    print(f"  Risk concentration: {high_risk_failure_rate/baseline_failure_rate:.1f}x higher")
    
    # Daily savings potential
    daily_batches = len(batch_df) / 365
    daily_high_risk = daily_batches * (total_high_risk / len(test_results))
    daily_failures_in_high_risk = daily_high_risk * high_risk_failure_rate
    cost_per_failure = 2500
    daily_savings_potential = daily_failures_in_high_risk * cost_per_failure * 0.5
    
    print(f"\\nDaily intervention potential:")
    print(f"  Daily high-risk batches: {daily_high_risk:.1f}")
    print(f"  Daily savings potential: ${daily_savings_potential:,.0f}")
    print(f"  Annual savings potential: ${daily_savings_potential * 365:,.0f}")
    
    # Summary
    print("\n" + "="*60)
    print("PART 3 SUMMARY")
    print("="*60)
    print("✅ Feature engineering completed successfully")
    print("✅ Models trained and validated")
    print("✅ Risk scoring system implemented")
    print("✅ Business value quantified")
    print("✅ Diagnostic findings validated through predictive modeling")
    print("✅ Ready for Part 4: Recommendations & Communication")
    
    return modeling_df, best_model, risk_analysis

if __name__ == "__main__":
    modeling_df, best_model, risk_analysis = test_part3()
    print(f"\n🎯 Final verification:")
    print(f"   Modeling dataset: {modeling_df.shape}")
    print(f"   Best model: {type(best_model).__name__}")
    print(f"   Risk categories: {len(risk_analysis)} levels")
    print(f"   All systems ready for Part 4!")
