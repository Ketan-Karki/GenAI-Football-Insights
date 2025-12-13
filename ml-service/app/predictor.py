import os
import psycopg2
import pandas as pd
import numpy as np
import joblib
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

class MatchPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model"""
        try:
            self.model = joblib.load('models/match_predictor.pkl')
            self.feature_names = joblib.load('models/feature_names.pkl')
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
    
    def get_db_connection(self):
        """Get database connection"""
        db_url = os.getenv('DATABASE_URL')
        return psycopg2.connect(db_url)
    
    def get_team_stats(self, team_external_id: int, competition_id: int | None = None):
        """Get team statistics from recent matches using external team id.

        We join through the teams table so we can pass the football-data.org
        team ID from the Go backend and still use the internal team IDs stored
        in the matches table.
        """
        conn = self.get_db_connection()

        query = """
            SELECT
                m.home_score,
                m.away_score,
                m.winner,
                m.utc_date,
                th.external_id AS home_external_id,
                ta.external_id AS away_external_id
            FROM matches m
            JOIN teams th ON m.home_team_id = th.id
            JOIN teams ta ON m.away_team_id = ta.id
            WHERE (th.external_id = %s OR ta.external_id = %s)
              AND m.status = 'FINISHED'
              AND m.home_score IS NOT NULL
            ORDER BY m.utc_date DESC
            LIMIT 10
        """

        df = pd.read_sql(query, conn, params=(team_external_id, team_external_id))
        conn.close()
        
        if len(df) == 0:
            # Return default stats if no history
            return {
                'form': 0.5,
                'goals_avg': 1.5,
                'conceded_avg': 1.5,
                'win_rate': 0.33
            }
        
        # Calculate stats
        wins = 0
        goals_scored: list[float] = []
        goals_conceded: list[float] = []

        for _, match in df.iterrows():
            is_home = match["home_external_id"] == team_external_id

            if is_home:
                goals_scored.append(match["home_score"])
                goals_conceded.append(match["away_score"])
                if match["winner"] == "HOME_TEAM":
                    wins += 1
            else:
                goals_scored.append(match["away_score"])
                goals_conceded.append(match["home_score"])
                if match["winner"] == "AWAY_TEAM":
                    wins += 1
        
        return {
            'form': wins / len(df) if len(df) > 0 else 0.5,
            'goals_avg': np.mean(goals_scored) if goals_scored else 1.5,
            'conceded_avg': np.mean(goals_conceded) if goals_conceded else 1.5,
            'win_rate': wins / len(df) if len(df) > 0 else 0.33
        }
    
    def predict(self, home_team_id, away_team_id, matchday=16):
        """Make prediction for a match using team statistics"""
        
        # Get team statistics
        home_stats = self.get_team_stats(home_team_id)
        away_stats = self.get_team_stats(away_team_id)
        
        # Calculate base probabilities from team statistics
        # Home advantage baseline
        home_base = 0.40
        draw_base = 0.27
        away_base = 0.33
        
        # Adjust based on form difference
        form_diff = home_stats['form'] - away_stats['form']
        home_base += form_diff * 0.3
        away_base -= form_diff * 0.3
        
        # Adjust based on goals scored
        goals_diff = home_stats['goals_avg'] - away_stats['goals_avg']
        home_base += goals_diff * 0.08
        away_base -= goals_diff * 0.08
        
        # Adjust based on defensive strength
        defense_diff = away_stats['conceded_avg'] - home_stats['conceded_avg']
        home_base += defense_diff * 0.06
        away_base -= defense_diff * 0.06
        
        # Add home advantage
        home_base += 0.12
        away_base -= 0.05
        
        # Normalize to ensure probabilities sum to 1
        total = home_base + draw_base + away_base
        home_win_prob = max(0.10, min(0.75, home_base / total))
        away_win_prob = max(0.10, min(0.75, away_base / total))
        draw_prob = max(0.15, 1.0 - home_win_prob - away_win_prob)
        
        # Renormalize
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total
        
        # Determine predicted outcome
        max_prob = max(away_win_prob, draw_prob, home_win_prob)
        if max_prob == home_win_prob:
            predicted_outcome = 'HOME_WIN'
        elif max_prob == away_win_prob:
            predicted_outcome = 'AWAY_WIN'
        else:
            predicted_outcome = 'DRAW'
        
        # Calculate confidence based on probability spread
        prob_spread = max_prob - min(away_win_prob, draw_prob, home_win_prob)
        confidence = min(0.95, 0.50 + prob_spread)
        
        return {
            'home_win_probability': round(home_win_prob, 3),
            'draw_probability': round(draw_prob, 3),
            'away_win_probability': round(away_win_prob, 3),
            'predicted_outcome': predicted_outcome,
            'confidence_score': round(confidence, 3),
            'model_version': 'v1.1.0-stats-based',
            'team_stats': {
                'home_form': round(home_stats['form'], 2),
                'away_form': round(away_stats['form'], 2),
                'home_goals_avg': round(home_stats['goals_avg'], 1),
                'away_goals_avg': round(away_stats['goals_avg'], 1),
                'home_win_rate': round(home_stats['win_rate'], 2),
                'away_win_rate': round(away_stats['win_rate'], 2)
            }
        }

# Global predictor instance
predictor = MatchPredictor()
