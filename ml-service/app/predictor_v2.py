"""
Team-Agnostic Predictor - Uses new neural network model
Replaces old position-based predictor with score prediction approach
"""

import numpy as np
from app.models.team_score_predictor import TeamScorePredictor
from app.feature_engineering import TeamAgnosticFeatureEngineer
from typing import Dict
import os

class TeamAgnosticPredictor:
    """Predictor using team-agnostic neural network"""
    
    def __init__(self):
        self.model = TeamScorePredictor()
        self.feature_engineer = TeamAgnosticFeatureEngineer()
        
        # Load trained model
        if not self.model.load():
            print("⚠️  Warning: Could not load trained model. Using fallback.")
    
    def predict(self, home_team_id: int, away_team_id: int, matchday: int = 1,
                home_team_name: str = None, away_team_name: str = None) -> Dict:
        """
        Predict match outcome using team-agnostic neural network.
        
        Args:
            home_team_id: Home team's external_id
            away_team_id: Away team's external_id
            matchday: Match day number
            home_team_name: Home team name for display
            away_team_name: Away team name for display
        
        Returns:
            Dict with predicted scores, outcome, confidence, and insights
        """
        try:
            # Get current date for feature extraction
            from datetime import datetime
            match_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract features for both teams
            home_features = self.feature_engineer.extract_features_for_team(
                team_id=home_team_id,
                opponent_id=away_team_id,
                match_date=match_date,
                is_at_venue=True
            )
            
            away_features = self.feature_engineer.extract_features_for_team(
                team_id=away_team_id,
                opponent_id=home_team_id,
                match_date=match_date,
                is_at_venue=False
            )
            
            # Predict using neural network
            result = self.model.predict_match(
                team_a_features=home_features,
                team_b_features=away_features,
                team_a_name=home_team_name or "Home Team",
                team_b_name=away_team_name or "Away Team"
            )
            
            # Generate insights
            insights = self._generate_insights(
                home_features=home_features,
                away_features=away_features,
                result=result,
                home_team_name=home_team_name,
                away_team_name=away_team_name
            )
            
            # Format response
            return {
                'predicted_outcome': result['predicted_outcome'],
                'predicted_winner': result['predicted_winner'],
                'team_a_predicted_goals': result['team_a_predicted_goals'],
                'team_b_predicted_goals': result['team_b_predicted_goals'],
                'confidence_score': result['confidence_score'],
                'goal_difference': result['goal_difference'],
                'model_version': 'team-agnostic-v1.0-neural-network',
                'insights': insights,
                'key_features': {
                    'home_quality': home_features['team_quality_rating'],
                    'away_quality': away_features['team_quality_rating'],
                    'home_xg': home_features['team_xg_per_game'],
                    'away_xg': away_features['team_xg_per_game'],
                    'quality_difference': home_features['quality_difference']
                }
            }
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            # Fallback to simple prediction
            return self._fallback_prediction(home_team_name, away_team_name)
    
    def _generate_insights(self, home_features: Dict, away_features: Dict, 
                          result: Dict, home_team_name: str, away_team_name: str) -> list:
        """Generate data-driven insights based on features and prediction"""
        insights = []
        
        winner = result['predicted_winner']
        home_goals = result['team_a_predicted_goals']
        away_goals = result['team_b_predicted_goals']
        
        # Quality-based insight
        quality_diff = home_features['quality_difference']
        if abs(quality_diff) > 15:
            stronger_team = home_team_name if quality_diff > 0 else away_team_name
            insights.append(f"{stronger_team} has significantly superior squad quality")
        
        # xG-based insight
        home_xg = home_features['team_xg_per_game']
        away_xg = away_features['team_xg_per_game']
        if home_xg > away_xg + 0.5:
            insights.append(f"{home_team_name} creates more scoring chances ({home_xg:.1f} vs {away_xg:.1f} xG/game)")
        elif away_xg > home_xg + 0.5:
            insights.append(f"{away_team_name} creates more scoring chances ({away_xg:.1f} vs {home_xg:.1f} xG/game)")
        
        # Form-based insight
        home_form = home_features['team_form_last_5']
        away_form = away_features['team_form_last_5']
        if home_form > away_form + 0.15:
            insights.append(f"{home_team_name} in better recent form")
        elif away_form > home_form + 0.15:
            insights.append(f"{away_team_name} in better recent form")
        
        # Score prediction insight
        if home_goals > away_goals + 1.5:
            insights.append(f"Expect {home_team_name} to dominate ({home_goals:.1f} - {away_goals:.1f})")
        elif away_goals > home_goals + 1.5:
            insights.append(f"Expect {away_team_name} to dominate ({home_goals:.1f} - {away_goals:.1f})")
        elif abs(home_goals - away_goals) < 0.5:
            insights.append(f"Closely contested match expected ({home_goals:.1f} - {away_goals:.1f})")
        
        # Confidence-based insight
        confidence = result['confidence_score']
        if confidence > 0.8:
            insights.append(f"High confidence in {winner} victory")
        elif confidence < 0.6:
            insights.append(f"Uncertain outcome - could go either way")
        
        return insights[:6]  # Return top 6 insights
    
    def _fallback_prediction(self, home_team_name: str, away_team_name: str) -> Dict:
        """Fallback prediction if model fails"""
        return {
            'predicted_outcome': 'Draw',
            'predicted_winner': 'Draw',
            'team_a_predicted_goals': 1.5,
            'team_b_predicted_goals': 1.5,
            'confidence_score': 0.5,
            'goal_difference': 0.0,
            'home_win_probability': 0.35,
            'draw_probability': 0.30,
            'away_win_probability': 0.35,
            'model_version': 'fallback-v1.0',
            'insights': ['Model unavailable - using fallback prediction'],
            'key_features': {}
        }


# Create global predictor instance
predictor = TeamAgnosticPredictor()
