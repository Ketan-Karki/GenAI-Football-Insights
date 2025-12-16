"""
Enhanced predictor that uses trained ML model with player statistics.
This predicts FUTURE matches using HISTORICAL data as features.
"""

import os
import joblib
import pandas as pd
import numpy as np
from app.feature_engineering import FeatureEngineer
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
                match_date: str = None, matchday: int = 1,
                home_team_name: str = None, away_team_name: str = None) -> dict:
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
            
            # Calculate confidence based on prediction certainty
            # Use entropy-based confidence: low entropy = high confidence
            # When probabilities are spread out (uncertain), entropy is high
            # When one probability dominates (certain), entropy is low
            sorted_probs = sorted(probabilities, reverse=True)
            
            # Calculate normalized entropy (0 = certain, 1 = maximum uncertainty)
            entropy = -sum(p * np.log(p + 1e-10) for p in probabilities if p > 0)
            max_entropy = np.log(len(probabilities))  # Maximum possible entropy
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            # Convert to confidence: high entropy = low confidence
            # Scale to range [0.55, 0.95] for better UX
            confidence = 0.95 - (normalized_entropy * 0.40)
            
            # Get feature values for insights
            features_dict = X.iloc[0].to_dict()
            
            # Generate insights based on features
            insights = self._generate_insights(features_dict, probabilities, home_team_name, away_team_name)
            
            result = {
                'home_win_probability': round(float(probabilities[2]), 3),
                'draw_probability': round(float(probabilities[1]), 3),
                'away_win_probability': round(float(probabilities[0]), 3),
                'predicted_outcome': predicted_outcome,
                'confidence_score': round(float(confidence), 3),
                'model_version': f"{self.metadata['model_type']}-v2.0-enhanced",
                'model_accuracy': round(self.metadata['accuracy'], 3),
                'insights': insights if insights else [],
                'key_features': self._get_key_features(features_dict)
            }
            return result
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return self._fallback_prediction(home_team_id, away_team_id)
    
    def _generate_insights(self, features: dict, probabilities: np.ndarray, 
                          home_team_name: str = None, away_team_name: str = None) -> list:
        """Generate insights that support the actual prediction outcome"""
        insights = []
        
        # Use team names if provided
        home_label = home_team_name if home_team_name else "Home team"
        away_label = away_team_name if away_team_name else "Away team"
        
        # Determine predicted outcome
        # probabilities order: [AWAY_WIN, DRAW, HOME_WIN]
        home_win_prob = probabilities[2]
        draw_prob = probabilities[1]
        away_win_prob = probabilities[0]
        
        predicted_winner = None
        if home_win_prob > draw_prob and home_win_prob > away_win_prob:
            predicted_winner = "home"
            winner_label = home_label
            loser_label = away_label
        elif away_win_prob > draw_prob and away_win_prob > home_win_prob:
            predicted_winner = "away"
            winner_label = away_label
            loser_label = home_label
        else:
            predicted_winner = "draw"
        
        # Generate insights that support the prediction
        if predicted_winner != "draw":
            # Get feature values
            form_diff = features.get('form_difference', 0)
            attack_diff = features.get('attack_strength_diff', 0)
            defense_diff = features.get('defense_strength_diff', 0)
            h2h_home_rate = features.get('h2h_home_win_rate', 0)
            h2h_away_rate = features.get('h2h_away_win_rate', 0)
            home_goals_pg = features.get('home_goals_per_game', 0)
            away_goals_pg = features.get('away_goals_per_game', 0)
            
            # Form insight - favor predicted winner
            if predicted_winner == "home" and form_diff > 0.1:
                insights.append(f"{winner_label} in better recent form")
            elif predicted_winner == "away" and form_diff < -0.1:
                insights.append(f"{winner_label} in better recent form")
            
            # Attack insight - favor predicted winner
            if predicted_winner == "home" and attack_diff > 0.2:
                insights.append(f"{winner_label} has stronger attacking threat ({home_goals_pg:.1f} goals/game)")
            elif predicted_winner == "away" and attack_diff < -0.2:
                insights.append(f"{winner_label} has stronger attacking threat ({away_goals_pg:.1f} goals/game)")
            
            # Defense insight - favor predicted winner
            if predicted_winner == "home" and defense_diff > 0.2:
                insights.append(f"{winner_label} more solid defensively")
            elif predicted_winner == "away" and defense_diff < -0.2:
                insights.append(f"{winner_label} more solid defensively")
            
            # H2H insight - only if it supports prediction
            if predicted_winner == "home" and h2h_home_rate > h2h_away_rate:
                insights.append(f"{winner_label} has historical advantage ({h2h_home_rate:.0%} win rate)")
            elif predicted_winner == "away" and h2h_away_rate > h2h_home_rate:
                insights.append(f"{winner_label} has historical advantage ({h2h_away_rate:.0%} win rate)")
            
            # Confidence level based on win probability
            win_prob = home_win_prob if predicted_winner == "home" else away_win_prob
            if win_prob > 0.7:
                insights.append(f"{winner_label} heavily favored to win")
            elif win_prob > 0.5:
                insights.append(f"{winner_label} slight edge in this matchup")
        else:
            # Draw prediction
            insights.append(f"Evenly matched teams")
            insights.append(f"📊 Draw probability: {draw_prob:.0%}")
            insights.append(f"Both teams showing competitive form")
        
        # Ensure we always have at least 3 insights
        if len(insights) < 3:
            insights.append(f"Expect a closely contested match")
            insights.append(f"Form and statistics suggest tight game")
        
        return insights[:6]  # Return top 6 insights
    
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
