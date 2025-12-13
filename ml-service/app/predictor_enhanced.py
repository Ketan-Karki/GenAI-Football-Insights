"""
Enhanced predictor that uses trained ML model with player statistics.
This predicts FUTURE matches using HISTORICAL data as features.
"""

import os
import joblib
import pandas as pd
import numpy as np
from feature_engineering import FeatureEngineer
from datetime import datetime

class EnhancedMatchPredictor:
    """
    ML-powered match predictor using historical team and player data.
    """
    
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.metadata = None
        self.engineer = FeatureEngineer()
        self.load_model()
    
    def load_model(self):
        """Load the trained ML model"""
        try:
            self.model = joblib.load('models/match_predictor_enhanced.pkl')
            self.feature_names = joblib.load('models/feature_names_enhanced.pkl')
            self.metadata = joblib.load('models/model_metadata.pkl')
            print(f"✅ Enhanced model loaded: {self.metadata['model_type']}")
            print(f"   Accuracy: {self.metadata['accuracy']:.2%}")
            print(f"   Features: {self.metadata['n_features']}")
        except FileNotFoundError:
            print("⚠️  Enhanced model not found. Using fallback predictor.")
            print("   Run 'python app/train_enhanced.py' to train the model.")
            self.model = None
    
    def predict(self, home_team_id: int, away_team_id: int, 
                match_date: str = None, matchday: int = 1) -> dict:
        """
        Predict match outcome using ML model trained on historical data.
        
        Args:
            home_team_id: Internal database ID of home team
            away_team_id: Internal database ID of away team
            match_date: Date of the match (defaults to today)
            matchday: Matchday number
            
        Returns:
            Dictionary with predictions, probabilities, and insights
        """
        
        if self.model is None:
            return self._fallback_prediction(home_team_id, away_team_id)
        
        # Use current date if not provided
        if match_date is None:
            match_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Extract features for this match
            X = self.engineer.extract_match_features(
                home_team_id, away_team_id, match_date, matchday
            )
            
            # Ensure feature order matches training
            X = X[self.feature_names]
            
            # Get predictions
            probabilities = self.model.predict_proba(X)[0]
            predicted_class = self.model.predict(X)[0]
            
            # Map to outcome labels
            outcome_map = {0: 'AWAY_WIN', 1: 'DRAW', 2: 'HOME_WIN'}
            predicted_outcome = outcome_map[predicted_class]
            
            # Calculate confidence
            max_prob = max(probabilities)
            confidence = min(0.95, max_prob)
            
            # Get feature values for insights
            features_dict = X.iloc[0].to_dict()
            
            # Generate insights based on features
            insights = self._generate_insights(features_dict, probabilities)
            
            return {
                'home_win_probability': round(float(probabilities[2]), 3),
                'draw_probability': round(float(probabilities[1]), 3),
                'away_win_probability': round(float(probabilities[0]), 3),
                'predicted_outcome': predicted_outcome,
                'confidence_score': round(float(confidence), 3),
                'model_version': f"{self.metadata['model_type']}-v2.0-enhanced",
                'model_accuracy': round(self.metadata['accuracy'], 3),
                'insights': insights,
                'key_features': self._get_key_features(features_dict)
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return self._fallback_prediction(home_team_id, away_team_id)
    
    def _generate_insights(self, features: dict, probabilities: np.ndarray) -> list:
        """Generate human-readable insights from features"""
        insights = []
        
        # Form analysis
        form_diff = features.get('form_difference', 0)
        if abs(form_diff) > 0.2:
            better_team = "Home" if form_diff > 0 else "Away"
            insights.append(
                f"{better_team} team in significantly better recent form "
                f"({abs(form_diff):.0%} advantage)"
            )
        
        # Attack strength
        attack_diff = features.get('attack_strength_diff', 0)
        if abs(attack_diff) > 0.5:
            stronger = "Home" if attack_diff > 0 else "Away"
            insights.append(
                f"{stronger} team averaging {abs(attack_diff):.1f} more goals per game"
            )
        
        # Player quality
        player_diff = features.get('player_quality_diff', 0)
        if abs(player_diff) > 0.3:
            better = "Home" if player_diff > 0 else "Away"
            insights.append(
                f"{better} team's key players in better scoring form"
            )
        
        # Head-to-head
        h2h_home_rate = features.get('h2h_home_win_rate', 0)
        h2h_away_rate = features.get('h2h_away_win_rate', 0)
        if h2h_home_rate > 0.6:
            insights.append(f"Home team dominates head-to-head ({h2h_home_rate:.0%} win rate)")
        elif h2h_away_rate > 0.6:
            insights.append(f"Away team dominates head-to-head ({h2h_away_rate:.0%} win rate)")
        
        # Defensive strength
        defense_diff = features.get('defense_strength_diff', 0)
        if abs(defense_diff) > 0.5:
            stronger = "Home" if defense_diff > 0 else "Away"
            insights.append(f"{stronger} team has stronger defense")
        
        # Prediction confidence
        max_prob = max(probabilities)
        if max_prob > 0.6:
            insights.append(f"High confidence prediction ({max_prob:.0%})")
        elif max_prob < 0.4:
            insights.append("Close match expected - outcome uncertain")
        
        return insights[:5]  # Return top 5 insights
    
    def _get_key_features(self, features: dict) -> dict:
        """Extract key features for display"""
        return {
            'home_form': round(features.get('home_form_score', 0), 2),
            'away_form': round(features.get('away_form_score', 0), 2),
            'home_goals_avg': round(features.get('home_goals_per_game', 0), 1),
            'away_goals_avg': round(features.get('away_goals_per_game', 0), 1),
            'home_player_goals': round(features.get('home_player_goals_avg', 0), 1),
            'away_player_goals': round(features.get('away_player_goals_avg', 0), 1),
            'h2h_home_wins': round(features.get('h2h_home_win_rate', 0) * 100, 0),
            'h2h_away_wins': round(features.get('h2h_away_win_rate', 0) * 100, 0)
        }
    
    def _fallback_prediction(self, home_team_id: int, away_team_id: int) -> dict:
        """Simple fallback when ML model is not available"""
        return {
            'home_win_probability': 0.40,
            'draw_probability': 0.30,
            'away_win_probability': 0.30,
            'predicted_outcome': 'HOME_WIN',
            'confidence_score': 0.50,
            'model_version': 'fallback-v1.0',
            'insights': ['ML model not trained yet. Using baseline prediction.']
        }

# Global instance
predictor = EnhancedMatchPredictor()
