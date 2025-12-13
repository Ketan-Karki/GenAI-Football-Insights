import os
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Database connection
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg2.connect(db_url)

# Feature engineering
def extract_features(df):
    """Extract features from match data for ML model"""
    features = pd.DataFrame()
    
    # Basic features
    features['home_team_id'] = df['home_team_id']
    features['away_team_id'] = df['away_team_id']
    features['matchday'] = df['matchday']
    
    # Calculate team form (last 5 matches)
    features['home_form'] = df.groupby('home_team_id')['home_win'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    features['away_form'] = df.groupby('away_team_id')['away_win'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    
    # Goals scored/conceded averages
    features['home_goals_avg'] = df.groupby('home_team_id')['home_score'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    features['away_goals_avg'] = df.groupby('away_team_id')['away_score'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    features['home_conceded_avg'] = df.groupby('home_team_id')['away_score'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    features['away_conceded_avg'] = df.groupby('away_team_id')['home_score'].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )
    
    # Home advantage indicator
    features['is_home'] = 1
    
    return features

# Load and prepare data
def load_training_data():
    """Load finished matches from database"""
    conn = get_db_connection()
    
    query = """
        SELECT 
            m.id,
            m.home_team_id,
            m.away_team_id,
            m.matchday,
            m.home_score,
            m.away_score,
            m.winner,
            m.utc_date,
            ht.name as home_team_name,
            at.name as away_team_name
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.id
        JOIN teams at ON m.away_team_id = at.id
        WHERE m.status = 'FINISHED'
          AND m.home_score IS NOT NULL
          AND m.away_score IS NOT NULL
        ORDER BY m.utc_date
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"📊 Loaded {len(df)} finished matches")
    
    # Create target variable
    df['home_win'] = (df['winner'] == 'HOME_TEAM').astype(int)
    df['away_win'] = (df['winner'] == 'AWAY_TEAM').astype(int)
    df['draw'] = (df['winner'].isna() | (df['winner'] == 'DRAW')).astype(int)
    
    # Create outcome label (0=away_win, 1=draw, 2=home_win)
    df['outcome'] = df.apply(lambda x: 2 if x['home_win'] else (0 if x['away_win'] else 1), axis=1)
    
    return df

# Train model
def train_model():
    """Train ML model on historical match data"""
    print("🚀 Starting ML model training...")
    
    # Load data
    df = load_training_data()
    
    if len(df) < 100:
        print("❌ Not enough data to train model (need at least 100 matches)")
        return
    
    # Extract features
    print("🔧 Engineering features...")
    X = extract_features(df)
    y = df['outcome']
    
    # Remove rows with NaN (first few matches won't have form data)
    mask = ~X.isna().any(axis=1)
    X = X[mask]
    y = y[mask]
    
    print(f"✅ Features extracted: {X.shape}")
    print(f"   - Home wins: {(y == 2).sum()}")
    print(f"   - Draws: {(y == 1).sum()}")
    print(f"   - Away wins: {(y == 0).sum()}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train Random Forest
    print("\n🌲 Training Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    # Train XGBoost
    print("🚀 Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_train, y_train)
    
    # Evaluate models
    print("\n📈 Evaluating models...")
    
    rf_pred = rf_model.predict(X_test)
    xgb_pred = xgb_model.predict(X_test)
    
    rf_acc = accuracy_score(y_test, rf_pred)
    xgb_acc = accuracy_score(y_test, xgb_pred)
    
    print(f"\n✅ Random Forest Accuracy: {rf_acc:.2%}")
    print(f"✅ XGBoost Accuracy: {xgb_acc:.2%}")
    
    # Use best model
    best_model = xgb_model if xgb_acc > rf_acc else rf_model
    best_name = "XGBoost" if xgb_acc > rf_acc else "Random Forest"
    best_acc = max(rf_acc, xgb_acc)
    
    print(f"\n🏆 Best model: {best_name} ({best_acc:.2%})")
    
    # Save model
    model_path = 'models/match_predictor.pkl'
    os.makedirs('models', exist_ok=True)
    joblib.dump(best_model, model_path)
    
    # Save feature names
    feature_names = X.columns.tolist()
    joblib.dump(feature_names, 'models/feature_names.pkl')
    
    print(f"\n💾 Model saved to {model_path}")
    print(f"💾 Feature names saved")
    
    # Print classification report
    print("\n📊 Detailed Classification Report:")
    print(classification_report(y_test, xgb_pred if xgb_acc > rf_acc else rf_pred,
                                target_names=['Away Win', 'Draw', 'Home Win']))
    
    print("\n🎉 Training complete!")
    return best_acc

if __name__ == "__main__":
    train_model()
