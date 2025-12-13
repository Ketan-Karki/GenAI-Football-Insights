import psycopg2
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os
from dotenv import load_dotenv

load_dotenv('../.env')

class FeatureEngineer:
    """
    Advanced feature engineering for football match prediction.
    Uses historical match data and player statistics to create predictive features.
    """
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url)
    
    def get_team_recent_form(self, team_id: int, before_date: str, n_matches: int = 5) -> Dict:
        """
        Calculate team's recent form from last N matches before a given date.
        Returns: wins, draws, losses, goals_for, goals_against, points
        """
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                m.home_score,
                m.away_score,
                m.winner,
                CASE 
                    WHEN m.home_team_id = %s THEN 'home'
                    ELSE 'away'
                END as team_position
            FROM matches m
            WHERE (m.home_team_id = %s OR m.away_team_id = %s)
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.home_score IS NOT NULL
            ORDER BY m.utc_date DESC
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(team_id, team_id, team_id, before_date, n_matches))
        conn.close()
        
        if len(df) == 0:
            return {
                'wins': 0, 'draws': 0, 'losses': 0,
                'goals_for': 0, 'goals_against': 0,
                'points': 0, 'form_score': 0.5,
                'matches_played': 0
            }
        
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for _, match in df.iterrows():
            is_home = match['team_position'] == 'home'
            
            if is_home:
                gf = match['home_score']
                ga = match['away_score']
            else:
                gf = match['away_score']
                ga = match['home_score']
            
            goals_for += gf
            goals_against += ga
            
            if match['winner'] == 'HOME_TEAM' and is_home:
                wins += 1
            elif match['winner'] == 'AWAY_TEAM' and not is_home:
                wins += 1
            elif match['winner'] == 'DRAW' or pd.isna(match['winner']):
                draws += 1
            else:
                losses += 1
        
        points = wins * 3 + draws
        form_score = points / (len(df) * 3) if len(df) > 0 else 0.5
        
        goals_pg = goals_for / len(df) if len(df) > 0 else 0
        conceded_pg = goals_against / len(df) if len(df) > 0 else 0
        
        return {
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'points': points,
            'form_score': form_score,
            'goals_per_game': goals_pg,
            'conceded_per_game': conceded_pg,
            'matches_played': len(df)
        }
    
    def get_player_features(self, team_id: int, before_date: str, n_matches: int = 5) -> Dict:
        """
        Get aggregated player statistics for a team from recent matches.
        Returns: avg goals per match, avg assists per match, top scorer form
        """
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                SUM(pms.goals) as total_goals,
                SUM(pms.assists) as total_assists,
                COUNT(DISTINCT pms.match_id) as matches_with_data,
                MAX(pms.goals) as max_goals_in_match,
                COUNT(DISTINCT pms.player_id) as active_players
            FROM player_match_stats pms
            JOIN players p ON pms.player_id = p.id
            JOIN matches m ON pms.match_id = m.id
            WHERE p.team_id = %s
              AND m.utc_date < %s
              AND m.status = 'FINISHED'
              AND pms.match_id IN (
                  SELECT m2.id FROM matches m2
                  WHERE m2.status = 'FINISHED'
                    AND m2.utc_date < %s
                  ORDER BY m2.utc_date DESC
                  LIMIT %s
              )
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date, before_date, n_matches * 20))
        conn.close()
        
        if len(df) == 0 or df.iloc[0]['matches_with_data'] == 0:
            return {
                'avg_goals_per_match': 0,
                'avg_assists_per_match': 0,
                'top_scorer_form': 0,
                'squad_depth': 0
            }
        
        row = df.iloc[0]
        matches = max(row['matches_with_data'], 1)
        
        return {
            'avg_goals_per_match': row['total_goals'] / matches if matches > 0 else 0,
            'avg_assists_per_match': row['total_assists'] / matches if matches > 0 else 0,
            'top_scorer_form': row['max_goals_in_match'] if row['max_goals_in_match'] else 0,
            'squad_depth': row['active_players'] if row['active_players'] else 0
        }
    
    def get_head_to_head(self, home_team_id: int, away_team_id: int, before_date: str, n_matches: int = 5) -> Dict:
        """
        Get head-to-head statistics between two teams.
        """
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                m.home_score,
                m.away_score,
                m.winner,
                m.home_team_id
            FROM matches m
            WHERE ((m.home_team_id = %s AND m.away_team_id = %s)
                OR (m.home_team_id = %s AND m.away_team_id = %s))
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.home_score IS NOT NULL
            ORDER BY m.utc_date DESC
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(
            home_team_id, away_team_id, 
            away_team_id, home_team_id,
            before_date, n_matches
        ))
        conn.close()
        
        if len(df) == 0:
            return {
                'h2h_home_wins': 0,
                'h2h_draws': 0,
                'h2h_away_wins': 0,
                'h2h_home_goals_avg': 0,
                'h2h_away_goals_avg': 0,
                'h2h_matches': 0
            }
        
        home_wins = away_wins = draws = 0
        home_goals = away_goals = 0
        
        for _, match in df.iterrows():
            # Determine which team was home in this historical match
            historical_home_is_current_home = match['home_team_id'] == home_team_id
            
            if historical_home_is_current_home:
                hg = match['home_score']
                ag = match['away_score']
            else:
                hg = match['away_score']
                ag = match['home_score']
            
            home_goals += hg
            away_goals += ag
            
            if match['winner'] == 'HOME_TEAM':
                if historical_home_is_current_home:
                    home_wins += 1
                else:
                    away_wins += 1
            elif match['winner'] == 'AWAY_TEAM':
                if historical_home_is_current_home:
                    away_wins += 1
                else:
                    home_wins += 1
            else:
                draws += 1
        
        return {
            'h2h_home_wins': home_wins,
            'h2h_draws': draws,
            'h2h_away_wins': away_wins,
            'h2h_home_goals_avg': home_goals / len(df) if len(df) > 0 else 0,
            'h2h_away_goals_avg': away_goals / len(df) if len(df) > 0 else 0,
            'h2h_matches': len(df)
        }
    
    def extract_match_features(self, home_team_id: int, away_team_id: int, 
                               match_date: str, matchday: int = 1) -> pd.DataFrame:
        """
        Extract all features for a single match prediction.
        This is used both for training (on historical data) and prediction (on future matches).
        """
        # Get team form
        home_form = self.get_team_recent_form(home_team_id, match_date, n_matches=10)
        away_form = self.get_team_recent_form(away_team_id, match_date, n_matches=10)
        
        # Get player statistics
        home_players = self.get_player_features(home_team_id, match_date, n_matches=5)
        away_players = self.get_player_features(away_team_id, match_date, n_matches=5)
        
        # Get head-to-head
        h2h = self.get_head_to_head(home_team_id, away_team_id, match_date, n_matches=5)
        
        # Compile features
        features = {
            # Match context
            'matchday': matchday,
            'is_home': 1,
            
            # Team form features (last 10 matches)
            'home_form_score': home_form['form_score'],
            'away_form_score': away_form['form_score'],
            'home_wins_recent': home_form['wins'],
            'away_wins_recent': away_form['wins'],
            'home_goals_per_game': home_form['goals_per_game'],
            'away_goals_per_game': away_form['goals_per_game'],
            'home_conceded_per_game': home_form['conceded_per_game'],
            'away_conceded_per_game': away_form['conceded_per_game'],
            
            # Player-based features
            'home_player_goals_avg': home_players['avg_goals_per_match'],
            'away_player_goals_avg': away_players['avg_goals_per_match'],
            'home_player_assists_avg': home_players['avg_assists_per_match'],
            'away_player_assists_avg': away_players['avg_assists_per_match'],
            'home_top_scorer_form': home_players['top_scorer_form'],
            'away_top_scorer_form': away_players['top_scorer_form'],
            
            # Head-to-head features
            'h2h_home_win_rate': h2h['h2h_home_wins'] / max(h2h['h2h_matches'], 1),
            'h2h_away_win_rate': h2h['h2h_away_wins'] / max(h2h['h2h_matches'], 1),
            'h2h_home_goals_avg': h2h['h2h_home_goals_avg'],
            'h2h_away_goals_avg': h2h['h2h_away_goals_avg'],
            
            # Derived features
            'form_difference': home_form['form_score'] - away_form['form_score'],
            'attack_strength_diff': home_form['goals_per_game'] - away_form['goals_per_game'],
            'defense_strength_diff': away_form['conceded_per_game'] - home_form['conceded_per_game'],
            'player_quality_diff': home_players['avg_goals_per_match'] - away_players['avg_goals_per_match'],
        }
        
        return pd.DataFrame([features])
    
    def extract_training_features(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extract features for all historical matches for model training.
        Returns: (X, y) where X is features and y is outcome labels
        """
        conn = self.get_db_connection()
        
        # Get all finished matches
        query = """
            SELECT 
                m.id,
                m.home_team_id,
                m.away_team_id,
                m.matchday,
                m.utc_date,
                m.winner,
                m.home_score,
                m.away_score
            FROM matches m
            WHERE m.status = 'FINISHED'
              AND m.home_score IS NOT NULL
              AND m.away_score IS NOT NULL
            ORDER BY m.utc_date
        """
        
        matches_df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"📊 Processing {len(matches_df)} matches for feature extraction...")
        
        all_features = []
        all_labels = []
        
        for idx, match in matches_df.iterrows():
            if idx % 100 == 0:
                print(f"   Processed {idx}/{len(matches_df)} matches...")
            
            try:
                # Extract features for this match
                features = self.extract_match_features(
                    match['home_team_id'],
                    match['away_team_id'],
                    match['utc_date'].strftime('%Y-%m-%d'),
                    match['matchday']
                )
                
                # Create label (0=away_win, 1=draw, 2=home_win)
                if match['winner'] == 'HOME_TEAM':
                    label = 2
                elif match['winner'] == 'AWAY_TEAM':
                    label = 0
                else:
                    label = 1
                
                all_features.append(features)
                all_labels.append(label)
                
            except Exception as e:
                print(f"   ⚠️  Error processing match {match['id']}: {e}")
                continue
        
        # Combine all features
        X = pd.concat(all_features, ignore_index=True)
        y = pd.Series(all_labels)
        
        print(f"✅ Feature extraction complete: {X.shape[0]} samples, {X.shape[1]} features")
        
        return X, y
