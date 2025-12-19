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
            
            # Check if this is an international match (teams with no historical data)
            has_home_data = self._check_team_has_data(home_team_id, match_date)
            has_away_data = self._check_team_has_data(away_team_id, match_date)
            
            # If both teams lack data (international match), use FIFA ranking-based prediction
            if not has_home_data and not has_away_data:
                return self._predict_international_match(home_team_name, away_team_name)
            
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
            
            # Calculate probabilities from score predictions for backward compatibility
            goal_diff = result['team_a_predicted_goals'] - result['team_b_predicted_goals']
            
            # Convert goal difference to win probabilities
            if goal_diff > 1.0:
                home_prob = min(0.85, 0.5 + (goal_diff * 0.15))
                away_prob = max(0.05, 0.5 - (goal_diff * 0.20))
                draw_prob = 1.0 - home_prob - away_prob
            elif goal_diff < -1.0:
                away_prob = min(0.85, 0.5 + (abs(goal_diff) * 0.15))
                home_prob = max(0.05, 0.5 - (abs(goal_diff) * 0.20))
                draw_prob = 1.0 - home_prob - away_prob
            else:
                # Close match
                home_prob = 0.5 + (goal_diff * 0.1)
                away_prob = 0.5 - (goal_diff * 0.1)
                draw_prob = max(0.2, 1.0 - home_prob - away_prob)
            
            # Format response
            return {
                'predicted_outcome': result['predicted_outcome'],
                'predicted_winner': result['predicted_winner'],
                'team_a_predicted_goals': result['team_a_predicted_goals'],
                'team_b_predicted_goals': result['team_b_predicted_goals'],
                'confidence_score': result['confidence_score'],
                'goal_difference': result['goal_difference'],
                'home_win_probability': round(home_prob, 2),
                'draw_probability': round(draw_prob, 2),
                'away_win_probability': round(away_prob, 2),
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
    
    def _check_team_has_data(self, team_id: int, match_date: str) -> bool:
        """Check if team has historical match data"""
        import psycopg2
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM matches m
            JOIN teams t ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s AND m.status = 'FINISHED'
        """, (team_id,))
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return count > 5
    
    def _predict_international_match(self, home_team_name: str, away_team_name: str) -> Dict:
        """Predict international match using FIFA rankings"""
        
        fifa_rankings = {
            'Brazil': 95, 'Argentina': 94, 'France': 93, 'England': 92, 'Spain': 91,
            'Germany': 90, 'Portugal': 89, 'Netherlands': 88, 'Belgium': 87, 'Italy': 86,
            'Croatia': 82, 'Uruguay': 81, 'Colombia': 80, 'Mexico': 79, 'Switzerland': 78,
            'USA': 77, 'Senegal': 76, 'Japan': 75, 'Morocco': 74, 'Korea Republic': 73,
            'Denmark': 72, 'Austria': 71, 'Ecuador': 70, 'Tunisia': 69, 'Poland': 68,
            'Australia': 65, 'Canada': 64, 'IR Iran': 63, 'Saudi Arabia': 62, 'Egypt': 61,
            'Norway': 60, 'Scotland': 59, 'Ghana': 58, 'Côte d\'Ivoire': 57, 'Algeria': 56,
            'South Africa': 55, 'Qatar': 54, 'Panama': 53, 'Paraguay': 52, 'Uzbekistan': 51,
            'Jordan': 48, 'Cabo Verde': 47, 'New Zealand': 46, 'Curaçao': 45, 'Haiti': 44,
        }
        
        home_strength = fifa_rankings.get(home_team_name, 60)
        away_strength = fifa_rankings.get(away_team_name, 60)
        strength_diff = home_strength - away_strength
        home_strength += 5
        
        home_goals = 1.0 + (home_strength / 50.0)
        away_goals = 1.0 + (away_strength / 50.0)
        
        total_strength = home_strength + away_strength
        home_prob = (home_strength / total_strength) * 0.7 + 0.15
        away_prob = (away_strength / total_strength) * 0.7 + 0.15
        draw_prob = 1.0 - home_prob - away_prob
        
        draw_prob = max(0.15, min(0.35, draw_prob))
        home_prob = max(0.20, min(0.70, home_prob))
        away_prob = 1.0 - home_prob - draw_prob
        
        if home_goals > away_goals + 0.3:
            predicted_outcome = f"{home_team_name} Win"
            predicted_winner = home_team_name
        elif away_goals > home_goals + 0.3:
            predicted_outcome = f"{away_team_name} Win"
            predicted_winner = away_team_name
        else:
            predicted_outcome = "Draw"
            predicted_winner = "Draw"
        
        insights = []
        if abs(strength_diff) > 15:
            stronger = home_team_name if strength_diff > 0 else away_team_name
            insights.append(f"{stronger} is significantly stronger (FIFA ranking)")
        elif abs(strength_diff) > 8:
            stronger = home_team_name if strength_diff > 0 else away_team_name
            insights.append(f"{stronger} has the edge in quality")
        else:
            insights.append("Evenly matched teams based on FIFA rankings")
        
        insights.append(f"Expected scoreline: {home_goals:.1f} - {away_goals:.1f}")
        
        return {
            'predicted_outcome': predicted_outcome,
            'predicted_winner': predicted_winner,
            'team_a_predicted_goals': round(home_goals, 1),
            'team_b_predicted_goals': round(away_goals, 1),
            'confidence_score': 0.65,
            'goal_difference': round(home_goals - away_goals, 1),
            'home_win_probability': round(home_prob, 2),
            'draw_probability': round(draw_prob, 2),
            'away_win_probability': round(away_prob, 2),
            'model_version': 'international-fifa-rankings-v1.0',
            'insights': insights,
            'key_features': {
                'home_strength': home_strength - 5,
                'away_strength': away_strength,
                'strength_difference': strength_diff
            }
        }
    
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
            'model_version': 'fallback-v1.0',
            'insights': ['Model unavailable - using fallback prediction'],
            'key_features': {}
        }


# Create global predictor instance
predictor = TeamAgnosticPredictor()
