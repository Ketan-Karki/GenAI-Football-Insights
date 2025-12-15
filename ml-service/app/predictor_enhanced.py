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
        """Generate human-readable insights from features with actual team names"""
        insights = []
        
        # Debug: print received team names
        print(f"🔍 Generating insights - Home: {home_team_name}, Away: {away_team_name}")
        
        # Use team names if provided, otherwise fall back to "Home"/"Away"
        home_label = home_team_name if home_team_name else "Home team"
        away_label = away_team_name if away_team_name else "Away team"
        
        # Form analysis - always show if there's any difference
        form_diff = features.get('form_difference', 0)
        if abs(form_diff) > 0.1:
            better_team = home_label if form_diff > 0 else away_label
            if abs(form_diff) > 0.3:
                insights.append(f"{better_team} in significantly better recent form")
            else:
                insights.append(f"{better_team} has slight form advantage")
        
        # Attack strength - always show
        attack_diff = features.get('attack_strength_diff', 0)
        if abs(attack_diff) > 0.3:
            stronger = home_label if attack_diff > 0 else away_label
            insights.append(f"{stronger} has stronger attacking threat ({abs(attack_diff):.1f} goals/game advantage)")
        elif abs(attack_diff) > 0.1:
            stronger = home_label if attack_diff > 0 else away_label
            insights.append(f"{stronger} slightly more potent in attack")
        
        # Defensive strength - always show
        defense_diff = features.get('defense_strength_diff', 0)
        if abs(defense_diff) > 0.3:
            stronger = home_label if defense_diff > 0 else away_label
            insights.append(f"{stronger} has superior defensive organization")
        elif abs(defense_diff) > 0.1:
            stronger = home_label if defense_diff > 0 else away_label
            insights.append(f"{stronger} slightly more solid defensively")
        
        # Midfield control (derived from possession/pass completion)
        possession_diff = features.get('possession_diff', 0)
        if abs(possession_diff) > 5:
            controller = home_label if possession_diff > 0 else away_label
            insights.append(f"{controller} likely to control midfield and possession")
        
        # Player quality and key players
        player_diff = features.get('player_quality_diff', 0)
        if abs(player_diff) > 0.2:
            better = home_label if player_diff > 0 else away_label
            insights.append(f"{better}'s key players in better form")
        
        # Head-to-head history
        h2h_home_rate = features.get('h2h_home_win_rate', 0)
        h2h_away_rate = features.get('h2h_away_win_rate', 0)
        if h2h_home_rate > 0.5:
            insights.append(f"{home_label} has historical advantage ({h2h_home_rate:.0%} win rate)")
        elif h2h_away_rate > 0.5:
            insights.append(f"{away_label} has historical advantage ({h2h_away_rate:.0%} win rate)")
        
        # Tactical matchup
        home_attack = features.get('home_goals_scored_avg', 0)
        away_defense = features.get('away_goals_conceded_avg', 0)
        if home_attack > 2.0 and away_defense > 1.5:
            insights.append(f"Tactical battle: {home_label}'s attack vs {away_label}'s vulnerable defense")
        
        # Prediction confidence
        max_prob = max(probabilities)
        if max_prob > 0.65:
            insights.append(f"High confidence prediction ({max_prob:.0%})")
        elif max_prob < 0.4:
            insights.append("Evenly matched - outcome highly uncertain")
        
        # Ensure we always have at least 3-5 insights
        if len(insights) < 3:
            insights.append(f"Both teams showing competitive form")
            insights.append(f"Expect a closely contested match")
        
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
