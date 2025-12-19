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
        """Predict international match using Elo-style ratings with form and tournament context"""
        
        # Elo-style ratings (1400-2100 scale) based on FIFA rankings and recent performance
        elo_ratings = {
            'Brazil': 2050, 'Argentina': 2040, 'France': 2030, 'England': 2020, 'Spain': 2010,
            'Germany': 1990, 'Portugal': 1980, 'Netherlands': 1970, 'Belgium': 1960, 'Italy': 1950,
            'Croatia': 1900, 'Uruguay': 1890, 'Colombia': 1880, 'Mexico': 1870, 'Switzerland': 1860,
            'USA': 1850, 'Senegal': 1840, 'Japan': 1830, 'Morocco': 1820, 'Korea Republic': 1810,
            'Denmark': 1800, 'Austria': 1790, 'Ecuador': 1780, 'Tunisia': 1770, 'Poland': 1760,
            'Australia': 1730, 'Canada': 1720, 'IR Iran': 1710, 'Saudi Arabia': 1700, 'Egypt': 1690,
            'Norway': 1680, 'Scotland': 1670, 'Ghana': 1660, 'Côte d\'Ivoire': 1650, 'Algeria': 1640,
            'South Africa': 1630, 'Qatar': 1620, 'Panama': 1610, 'Paraguay': 1600, 'Uzbekistan': 1590,
            'Jordan': 1560, 'Cabo Verde': 1550, 'New Zealand': 1540, 'Curaçao': 1530, 'Haiti': 1520,
        }
        
        home_elo = elo_ratings.get(home_team_name, 1700)
        away_elo = elo_ratings.get(away_team_name, 1700)
        
        # Home advantage in Elo points (smaller for neutral venues in World Cup)
        home_advantage = 50
        adjusted_home_elo = home_elo + home_advantage
        
        # Logistic win probability based on Elo difference
        elo_diff = adjusted_home_elo - away_elo
        home_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        away_win_prob = 1 - home_win_prob
        
        # Expected goals using Poisson-inspired model
        # Convert Elo to expected goals (1400=0.8, 1700=1.5, 2000=2.2 goals)
        home_xg = 0.8 + ((adjusted_home_elo - 1400) / 300)
        away_xg = 0.8 + ((away_elo - 1400) / 300)
        
        # Adjust probabilities to include draws (Poisson-based)
        # Draw probability peaks when teams are evenly matched
        draw_factor = max(0, 1 - abs(elo_diff) / 200)
        base_draw_prob = 0.25 * draw_factor + 0.15
        
        # Normalize probabilities
        total = home_win_prob + away_win_prob + base_draw_prob
        home_prob = home_win_prob / total
        away_prob = away_win_prob / total
        draw_prob = base_draw_prob / total
        
        # Choose winner based on highest probability
        max_prob = max(home_prob, away_prob, draw_prob)
        if max_prob == home_prob:
            predicted_outcome = f"{home_team_name} Win"
            predicted_winner = home_team_name
            confidence = 0.5 + min(0.4, (home_prob - 0.5))
        elif max_prob == away_prob:
            predicted_outcome = f"{away_team_name} Win"
            predicted_winner = away_team_name
            confidence = 0.5 + min(0.4, (away_prob - 0.5))
        else:
            predicted_outcome = "Draw"
            predicted_winner = "Draw"
            confidence = 0.5 + min(0.3, (draw_prob - 0.25))
        
        # Generate insights based on Elo and xG
        insights = []
        if abs(elo_diff) > 200:
            stronger = home_team_name if elo_diff > 0 else away_team_name
            insights.append(f"{stronger} has significantly superior squad quality (Elo: {abs(elo_diff):.0f} point advantage)")
        elif abs(elo_diff) > 100:
            stronger = home_team_name if elo_diff > 0 else away_team_name
            insights.append(f"{stronger} has the edge in quality (Elo: {abs(elo_diff):.0f} points)")
        else:
            insights.append(f"Evenly matched teams (Elo difference: {abs(elo_diff):.0f} points)")
        
        if home_xg > away_xg + 0.5:
            insights.append(f"{home_team_name} expected to create more chances ({home_xg:.1f} vs {away_xg:.1f} xG)")
        elif away_xg > home_xg + 0.5:
            insights.append(f"{away_team_name} expected to create more chances ({away_xg:.1f} vs {home_xg:.1f} xG)")
        
        insights.append(f"Predicted scoreline: {home_xg:.1f} - {away_xg:.1f}")
        
        return {
            'predicted_outcome': predicted_outcome,
            'predicted_winner': predicted_winner,
            'team_a_predicted_goals': round(home_xg, 1),
            'team_b_predicted_goals': round(away_xg, 1),
            'confidence_score': round(confidence, 2),
            'goal_difference': round(home_xg - away_xg, 1),
            'home_win_probability': round(home_prob, 2),
            'draw_probability': round(draw_prob, 2),
            'away_win_probability': round(away_prob, 2),
            'model_version': 'international-elo-xg-v2.0',
            'insights': insights,
            'key_features': {
                'home_elo': home_elo,
                'away_elo': away_elo,
                'elo_difference': elo_diff,
                'home_xg': round(home_xg, 2),
                'away_xg': round(away_xg, 2)
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
        predicted_winner = result.get('predicted_winner', winner)
        if confidence > 0.8:
            insights.append(f"High confidence in {predicted_winner} victory")
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
