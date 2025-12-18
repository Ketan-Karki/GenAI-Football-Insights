"""
Training Script for Team-Agnostic Score Prediction Model
Uses existing database data with derived xG-like features.
"""

import numpy as np
import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
from dotenv import load_dotenv
from models.team_score_predictor import TeamScorePredictor
from datetime import datetime

load_dotenv()

class TeamAgnosticTrainer:
    """Train team-agnostic neural network on historical match data"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.predictor = TeamScorePredictor()
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url)
    
    def prepare_training_data(self):
        """
        Prepare training data from database.
        Creates symmetric samples: each match generates 2 samples (one per team).
        """
        print("\n" + "="*60)
        print("PREPARING TRAINING DATA")
        print("="*60)
        
        conn = self.get_db_connection()
        
        # Get finished matches with scores
        query = """
            SELECT 
                m.id as match_id,
                m.utc_date,
                m.home_score,
                m.away_score,
                ht.external_id as home_team_id,
                at.external_id as away_team_id,
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
        
        matches_df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"✓ Loaded {len(matches_df)} finished matches")
        
        # Prepare features and labels
        X_samples = []
        y_samples = []
        
        print("\nExtracting features...")
        
        for idx, match in matches_df.iterrows():
            if idx % 100 == 0:
                print(f"  Processed {idx}/{len(matches_df)} matches...")
            
            try:
                # Sample 1: Home team perspective
                home_features = self._extract_team_features(
                    team_id=match['home_team_id'],
                    opponent_id=match['away_team_id'],
                    match_date=match['utc_date'].strftime('%Y-%m-%d'),
                    is_at_venue=True
                )
                X_samples.append(list(home_features.values()))
                y_samples.append(match['home_score'])
                
                # Sample 2: Away team perspective (symmetric)
                away_features = self._extract_team_features(
                    team_id=match['away_team_id'],
                    opponent_id=match['home_team_id'],
                    match_date=match['utc_date'].strftime('%Y-%m-%d'),
                    is_at_venue=False
                )
                X_samples.append(list(away_features.values()))
                y_samples.append(match['away_score'])
                
            except Exception as e:
                print(f"  ⚠️  Error processing match {match['match_id']}: {e}")
                continue
        
        X = np.array(X_samples)
        y = np.array(y_samples)
        
        print(f"\n✓ Prepared {len(X)} training samples ({len(matches_df)} matches × 2)")
        print(f"✓ Feature dimensions: {X.shape}")
        print(f"✓ Label dimensions: {y.shape}")
        
        return X, y
    
    def _extract_team_features(self, team_id: int, opponent_id: int, 
                               match_date: str, is_at_venue: bool) -> dict:
        """
        Extract 31 features for a team using existing database data.
        Uses derived xG-like metrics from actual performance.
        """
        conn = self.get_db_connection()
        
        features = {}
        
        # 1-2. Team Quality Ratings
        team_quality = self._get_team_quality(conn, team_id, match_date)
        opponent_quality = self._get_team_quality(conn, opponent_id, match_date)
        features['team_quality_rating'] = team_quality
        features['opponent_quality_rating'] = opponent_quality
        
        # 3-10. Attacking Features (derived from actual performance)
        team_attack = self._get_attacking_stats(conn, team_id, match_date)
        features['team_xg_per_game'] = team_attack['derived_xg']
        features['team_goals_per_game'] = team_attack['goals_per_game']
        features['team_shots_per_game'] = team_attack['shots_per_game']
        features['team_striker_xg'] = team_attack['top_scorer_rate']
        features['team_playmaker_assists'] = team_attack['assists_per_game']
        features['team_formation_attack'] = team_attack['attack_rating']
        features['team_pressing_intensity'] = team_attack['pressing_score']
        features['team_possession_avg'] = team_attack['possession_estimate']
        
        # 11-16. Defensive Features
        opponent_defense = self._get_defensive_stats(conn, opponent_id, match_date)
        features['opponent_xg_conceded'] = opponent_defense['derived_xg_conceded']
        features['opponent_goals_conceded'] = opponent_defense['goals_conceded_per_game']
        features['opponent_defensive_rating'] = opponent_defense['defense_rating']
        features['opponent_goalkeeper_save_pct'] = opponent_defense['save_rate']
        features['opponent_tackles_per_game'] = opponent_defense['tackles_estimate']
        features['opponent_formation_defense'] = opponent_defense['defense_formation_score']
        
        # 17-20. Match Context
        features['venue_factor'] = 1.0 if is_at_venue else 0.85
        features['rest_days'] = self._get_rest_days(conn, team_id, match_date)
        features['travel_distance'] = 0 if is_at_venue else 200
        features['injury_impact'] = 0  # TODO: Add when player_availability is populated
        
        # 21-23. Head-to-Head
        h2h = self._get_h2h_stats(conn, team_id, opponent_id, match_date)
        features['h2h_goals_scored_avg'] = h2h['goals_scored']
        features['h2h_goals_conceded_avg'] = h2h['goals_conceded']
        features['h2h_win_rate'] = h2h['win_rate']
        
        # 24-27. Form
        form = self._get_form_stats(conn, team_id, match_date)
        features['team_form_last_5'] = form['form_5']
        features['team_form_last_10'] = form['form_10']
        features['team_momentum'] = form['momentum']
        
        opponent_form = self._get_form_stats(conn, opponent_id, match_date)
        features['opponent_form_last_5'] = opponent_form['form_5']
        
        # 28-29. Tactical
        features['coach_win_rate'] = 0.5  # TODO: Add when coaches table is populated
        features['tactical_matchup_score'] = 5.0
        
        # 30-31. Derived
        features['quality_difference'] = team_quality - opponent_quality
        features['attack_vs_defense'] = features['team_xg_per_game'] - features['opponent_xg_conceded']
        
        conn.close()
        return features
    
    def _get_team_quality(self, conn, team_id: int, before_date: str) -> float:
        """Calculate team quality (0-100) from season performance"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN (m.home_team_id = t.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t.id AND m.winner = 'AWAY_TEAM') 
                    THEN 1 ELSE 0 END) as wins,
                AVG(CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE m.away_score END) as goals_scored,
                AVG(CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END) as goals_conceded
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '365 days')
              AND m.home_score IS NOT NULL
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date, before_date))
        
        if len(df) == 0 or df.iloc[0]['total'] == 0:
            return 50.0
        
        row = df.iloc[0]
        win_rate = (row['wins'] / row['total']) * 100
        goal_diff = (row['goals_scored'] - row['goals_conceded']) if row['goals_scored'] else 0
        goal_score = min(100, max(0, 50 + (goal_diff * 10)))
        
        return round((win_rate * 0.6) + (goal_score * 0.4), 2)
    
    def _get_attacking_stats(self, conn, team_id: int, before_date: str) -> dict:
        """Get attacking stats with derived xG"""
        query = """
            SELECT 
                AVG(CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE m.away_score END) as goals_per_game,
                COUNT(*) as matches
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '180 days')
              AND m.home_score IS NOT NULL
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date, before_date))
        
        goals_pg = df.iloc[0]['goals_per_game'] if len(df) > 0 and df.iloc[0]['goals_per_game'] else 1.5
        
        # Derived xG: estimate based on goals (xG typically ~0.9-1.1x actual goals)
        derived_xg = goals_pg * 1.05
        
        return {
            'derived_xg': derived_xg,
            'goals_per_game': goals_pg,
            'shots_per_game': goals_pg * 8,  # Estimate: ~8 shots per goal
            'top_scorer_rate': goals_pg * 0.4,  # Top scorer gets ~40% of goals
            'assists_per_game': goals_pg * 0.7,  # ~70% of goals are assisted
            'attack_rating': min(10, goals_pg * 3),
            'pressing_score': 5.0,
            'possession_estimate': 50.0
        }
    
    def _get_defensive_stats(self, conn, team_id: int, before_date: str) -> dict:
        """Get defensive stats with derived xG conceded"""
        query = """
            SELECT 
                AVG(CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END) as goals_conceded
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '180 days')
              AND m.home_score IS NOT NULL
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date, before_date))
        
        goals_conceded = df.iloc[0]['goals_conceded'] if len(df) > 0 and df.iloc[0]['goals_conceded'] else 1.5
        
        return {
            'derived_xg_conceded': goals_conceded * 1.05,
            'goals_conceded_per_game': goals_conceded,
            'defense_rating': max(0, 10 - goals_conceded * 3),
            'save_rate': max(0.5, 0.8 - (goals_conceded * 0.1)),
            'tackles_estimate': 15.0,
            'defense_formation_score': 5.0
        }
    
    def _get_rest_days(self, conn, team_id: int, match_date: str) -> int:
        """Calculate rest days"""
        query = """
            SELECT MAX(m.utc_date) as last_match
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
        """
        
        df = pd.read_sql(query, conn, params=(team_id, match_date))
        
        if len(df) > 0 and df.iloc[0]['last_match']:
            last = pd.to_datetime(df.iloc[0]['last_match'])
            current = pd.to_datetime(match_date)
            return min((current - last).days, 14)
        
        return 7
    
    def _get_h2h_stats(self, conn, team_id: int, opponent_id: int, before_date: str) -> dict:
        """Get head-to-head stats"""
        query = """
            SELECT 
                AVG(CASE WHEN m.home_team_id = t1.id THEN m.home_score ELSE m.away_score END) as goals_scored,
                AVG(CASE WHEN m.home_team_id = t1.id THEN m.away_score ELSE m.home_score END) as goals_conceded,
                SUM(CASE 
                    WHEN (m.home_team_id = t1.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t1.id AND m.winner = 'AWAY_TEAM') 
                    THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0)::float as win_rate
            FROM teams t1, teams t2, matches m
            WHERE t1.external_id = %s
              AND t2.external_id = %s
              AND ((m.home_team_id = t1.id AND m.away_team_id = t2.id) OR
                   (m.away_team_id = t1.id AND m.home_team_id = t2.id))
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '730 days')
        """
        
        df = pd.read_sql(query, conn, params=(team_id, opponent_id, before_date, before_date))
        
        if len(df) > 0 and df.iloc[0]['goals_scored'] is not None:
            return {
                'goals_scored': float(df.iloc[0]['goals_scored']),
                'goals_conceded': float(df.iloc[0]['goals_conceded']),
                'win_rate': float(df.iloc[0]['win_rate']) if df.iloc[0]['win_rate'] else 0.5
            }
        
        return {'goals_scored': 1.5, 'goals_conceded': 1.5, 'win_rate': 0.5}
    
    def _get_form_stats(self, conn, team_id: int, before_date: str) -> dict:
        """Get form stats"""
        query = """
            WITH recent_matches AS (
                SELECT 
                    CASE 
                        WHEN (m.home_team_id = t.id AND m.winner = 'HOME_TEAM') OR 
                             (m.away_team_id = t.id AND m.winner = 'AWAY_TEAM') 
                        THEN 3
                        WHEN m.winner = 'DRAW' THEN 1
                        ELSE 0 
                    END as points,
                    ROW_NUMBER() OVER (ORDER BY m.utc_date DESC) as match_num
                FROM teams t
                JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
                WHERE t.external_id = %s
                  AND m.status = 'FINISHED'
                  AND m.utc_date < %s
                LIMIT 10
            )
            SELECT 
                AVG(CASE WHEN match_num <= 5 THEN points END) / 3.0 as form_5,
                AVG(points) / 3.0 as form_10
            FROM recent_matches
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date))
        
        if len(df) > 0:
            form_5 = float(df.iloc[0]['form_5']) if df.iloc[0]['form_5'] else 0.5
            form_10 = float(df.iloc[0]['form_10']) if df.iloc[0]['form_10'] else 0.5
            return {
                'form_5': form_5,
                'form_10': form_10,
                'momentum': form_5 - form_10
            }
        
        return {'form_5': 0.5, 'form_10': 0.5, 'momentum': 0.0}
    
    def train(self):
        """Train the team-agnostic neural network"""
        print("\n" + "="*60)
        print("TRAINING TEAM-AGNOSTIC SCORE PREDICTION MODEL")
        print("="*60)
        
        # Prepare data
        X, y = self.prepare_training_data()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"\n✓ Training set: {len(X_train)} samples")
        print(f"✓ Test set: {len(X_test)} samples")
        
        # Train model
        print("\nTraining neural network...")
        history = self.predictor.train(X_train, y_train, epochs=100, batch_size=32)
        
        # Evaluate
        print("\nEvaluating model...")
        metrics = self.predictor.evaluate(X_test, y_test)
        
        print("\n" + "="*60)
        print("MODEL PERFORMANCE")
        print("="*60)
        print(f"✓ Mean Absolute Error: {metrics['mae']:.3f} goals")
        print(f"✓ Root Mean Squared Error: {metrics['rmse']:.3f} goals")
        print(f"✓ Accuracy within 1 goal: {metrics['accuracy_within_1_goal']*100:.1f}%")
        
        # Save model
        print("\nSaving model...")
        self.predictor.save()
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Model saved to: {self.predictor.model_path}")
        print(f"Scaler saved to: {self.predictor.scaler_path}")


if __name__ == "__main__":
    trainer = TeamAgnosticTrainer()
    trainer.train()
