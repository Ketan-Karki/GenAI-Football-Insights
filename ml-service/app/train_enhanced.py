"""
Enhanced ML training script with player statistics and advanced features.
This trains a model on HISTORICAL data to predict FUTURE match outcomes.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
from feature_engineering import FeatureEngineer
import matplotlib.pyplot as plt
import seaborn as sns

def train_enhanced_model():
    """Train ML model with enhanced features including player statistics"""
    
    print("=" * 60)
    print("🚀 ENHANCED ML MODEL TRAINING")
    print("=" * 60)
    print("\n📊 Using historical match data + player statistics")
    print("🎯 Goal: Predict future match outcomes\n")
    
    # Initialize feature engineer
    engineer = FeatureEngineer()
    
    # Extract features from all historical matches
    print("🔧 Step 1: Feature Engineering")
    print("-" * 60)
    X, y = engineer.extract_training_features()
    
    # Remove any rows with NaN values
    print(f"\n🧹 Cleaning data...")
    mask = ~X.isna().any(axis=1)
    X = X[mask]
    y = y[mask]
    
    print(f"✅ Clean dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"\n📈 Class distribution:")
    print(f"   - Home wins: {(y == 2).sum()} ({(y == 2).sum() / len(y) * 100:.1f}%)")
    print(f"   - Draws: {(y == 1).sum()} ({(y == 1).sum() / len(y) * 100:.1f}%)")
    print(f"   - Away wins: {(y == 0).sum()} ({(y == 0).sum() / len(y) * 100:.1f}%)")
    
    # Split data (80/20 train/test)
    print(f"\n📊 Step 2: Train/Test Split")
    print("-" * 60)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"✅ Training set: {len(X_train)} samples")
    print(f"✅ Test set: {len(X_test)} samples")
    
    # Train multiple models
    print(f"\n🤖 Step 3: Model Training")
    print("-" * 60)
    
    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        ),
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\n🔄 Training {name}...")
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Accuracy
        acc = accuracy_score(y_test, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        
        results[name] = {
            'model': model,
            'accuracy': acc,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'predictions': y_pred
        }
        
        print(f"   ✅ Test Accuracy: {acc:.2%}")
        print(f"   ✅ CV Accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std():.2%})")
    
    # Select best model
    best_model_name = max(results, key=lambda x: results[x]['accuracy'])
    best_model = results[best_model_name]['model']
    best_acc = results[best_model_name]['accuracy']
    
    print(f"\n🏆 Step 4: Best Model Selection")
    print("-" * 60)
    print(f"✅ Winner: {best_model_name}")
    print(f"✅ Test Accuracy: {best_acc:.2%}")
    print(f"✅ CV Accuracy: {results[best_model_name]['cv_mean']:.2%}")
    
    # Feature importance
    print(f"\n📊 Step 5: Feature Importance Analysis")
    print("-" * 60)
    
    if hasattr(best_model, 'feature_importances_'):
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': best_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔝 Top 10 Most Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"   {row['feature']:30s} {row['importance']:.4f}")
        
        # Save feature importance
        feature_importance.to_csv('models/feature_importance.csv', index=False)
    
    # Detailed classification report
    print(f"\n📋 Step 6: Detailed Performance Report")
    print("-" * 60)
    print(classification_report(
        y_test, 
        results[best_model_name]['predictions'],
        target_names=['Away Win', 'Draw', 'Home Win'],
        digits=3
    ))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, results[best_model_name]['predictions'])
    print("\n📊 Confusion Matrix:")
    print("                Predicted")
    print("              Away  Draw  Home")
    print(f"Actual Away   {cm[0][0]:4d}  {cm[0][1]:4d}  {cm[0][2]:4d}")
    print(f"       Draw   {cm[1][0]:4d}  {cm[1][1]:4d}  {cm[1][2]:4d}")
    print(f"       Home   {cm[2][0]:4d}  {cm[2][1]:4d}  {cm[2][2]:4d}")
    
    # Save model
    print(f"\n💾 Step 7: Saving Model")
    print("-" * 60)
    
    os.makedirs('models', exist_ok=True)
    
    model_path = 'models/match_predictor_enhanced.pkl'
    joblib.dump(best_model, model_path)
    print(f"✅ Model saved: {model_path}")
    
    feature_names_path = 'models/feature_names_enhanced.pkl'
    joblib.dump(X.columns.tolist(), feature_names_path)
    print(f"✅ Features saved: {feature_names_path}")
    
    # Save metadata
    metadata = {
        'model_type': best_model_name,
        'accuracy': best_acc,
        'cv_accuracy': results[best_model_name]['cv_mean'],
        'n_features': len(X.columns),
        'n_training_samples': len(X_train),
        'n_test_samples': len(X_test),
        'feature_names': X.columns.tolist()
    }
    joblib.dump(metadata, 'models/model_metadata.pkl')
    print(f"✅ Metadata saved: models/model_metadata.pkl")
    
    print("\n" + "=" * 60)
    print("🎉 TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\n✅ Model: {best_model_name}")
    print(f"✅ Accuracy: {best_acc:.2%}")
    print(f"✅ Features: {len(X.columns)} (including player statistics)")
    print(f"✅ Training samples: {len(X_train)}")
    print(f"\n🚀 Ready to predict future matches!")
    print("=" * 60)
    
    return best_model, best_acc, metadata

if __name__ == "__main__":
    train_enhanced_model()
