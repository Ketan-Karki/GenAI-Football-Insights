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
    
    def get_team_recent_form(self, team_external_id: int, before_date: str, n_matches: int = 5) -> Dict:
        """
        Calculate team's recent form from last N matches before a given date.
        Uses external_id (from API) to identify teams.
        Returns: wins, draws, losses, goals_for, goals_against, points
        """
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                m.home_score,
                m.away_score,
                m.winner,
                ht.external_id as home_team_ext_id,
                at.external_id as away_team_ext_id
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE (ht.external_id = %s OR at.external_id = %s)
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.home_score IS NOT NULL
            ORDER BY m.utc_date DESC
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(team_external_id, team_external_id, before_date, n_matches))
        conn.close()
        
        if len(df) == 0:
            return {
                'wins': 0, 'draws': 0, 'losses': 0,
                'goals_for': 0, 'goals_against': 0,
                'points': 0, 'form_score': 0.5,
                'goals_per_game': 0,
                'conceded_per_game': 0,
                'matches_played': 0
            }
        
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for _, match in df.iterrows():
            is_home = match['home_team_ext_id'] == team_external_id
            
            if is_home:
                goals_for += match['home_score']
                goals_against += match['away_score']
            else:
                goals_for += match['away_score']
                goals_against += match['home_score']
            
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
    
    def get_player_features(self, team_external_id: int, before_date: str, n_matches: int = 5) -> Dict:
        """
        Get aggregated player statistics for a team from recent matches.
        Uses external_id (from API) to identify teams.
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
            JOIN teams t ON p.team_id = t.id
            JOIN matches m ON pms.match_id = m.id
            WHERE t.external_id = %s
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
        
        df = pd.read_sql(query, conn, params=(team_external_id, before_date, before_date, n_matches * 20))
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
    
    def get_head_to_head(self, home_team_ext_id: int, away_team_ext_id: int, 
                         before_date: str, n_matches: int = 5) -> Dict:
        """
        Get head-to-head record between two teams.
        Uses external_id (from API) to identify teams.
        Returns: home wins, away wins, draws, avg goals
        """
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                m.home_score, m.away_score, m.winner,
                ht.external_id as home_team_ext_id,
                at.external_id as away_team_ext_id
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE ((ht.external_id = %s AND at.external_id = %s)
                OR (ht.external_id = %s AND at.external_id = %s))
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
            ORDER BY m.utc_date DESC
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(
            home_team_ext_id, away_team_ext_id,
            away_team_ext_id, home_team_ext_id,
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
        
        h2h_home_wins = h2h_away_wins = h2h_draws = 0
        h2h_home_goals = h2h_away_goals = 0
        
        for _, match in df.iterrows():
            # From perspective of current home team
            if match['home_team_ext_id'] == home_team_ext_id:
                h2h_home_goals += match['home_score']
                h2h_away_goals += match['away_score']
                if match['winner'] == 'HOME_TEAM':
                    h2h_home_wins += 1
                elif match['winner'] == 'AWAY_TEAM':
                    h2h_away_wins += 1
                else:
                    h2h_draws += 1
            else:
                h2h_home_goals += match['away_score']
                h2h_away_goals += match['home_score']
                if match['winner'] == 'AWAY_TEAM':
                    h2h_home_wins += 1
                elif match['winner'] == 'HOME_TEAM':
                    h2h_away_wins += 1
                else:
                    h2h_draws += 1
        
        return {
            'h2h_home_wins': h2h_home_wins,
            'h2h_draws': h2h_draws,
            'h2h_away_wins': h2h_away_wins,
            'h2h_home_goals_avg': h2h_home_goals / len(df) if len(df) > 0 else 0,
            'h2h_away_goals_avg': h2h_away_goals / len(df) if len(df) > 0 else 0,
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
            
            # Team form features
            'home_form_score': home_form.get('form_score', 0.5),
            'away_form_score': away_form.get('form_score', 0.5),
            'home_wins_recent': home_form.get('wins', 0),
            'away_wins_recent': away_form.get('wins', 0),
            'home_goals_per_game': home_form.get('goals_per_game', 0),
            'away_goals_per_game': away_form.get('goals_per_game', 0),
            'home_conceded_per_game': home_form.get('conceded_per_game', 0),
            'away_conceded_per_game': away_form.get('conceded_per_game', 0),
            
            # Player-based features
            'home_player_goals_avg': home_players.get('avg_goals_per_match', 0),
            'away_player_goals_avg': away_players.get('avg_goals_per_match', 0),
            'home_player_assists_avg': home_players.get('avg_assists_per_match', 0),
            'away_player_assists_avg': away_players.get('avg_assists_per_match', 0),
            'home_top_scorer_form': home_players.get('top_scorer_form', 0),
            'away_top_scorer_form': away_players.get('top_scorer_form', 0),
            
            # Head-to-head features
            'h2h_home_win_rate': h2h.get('h2h_home_wins', 0) / max(h2h.get('h2h_matches', 1), 1),
            'h2h_away_win_rate': h2h.get('h2h_away_wins', 0) / max(h2h.get('h2h_matches', 1), 1),
            'h2h_home_goals_avg': h2h.get('h2h_home_goals_avg', 0),
            'h2h_away_goals_avg': h2h.get('h2h_away_goals_avg', 0),
            
            # Derived features
            'form_difference': home_form.get('form_score', 0.5) - away_form.get('form_score', 0.5),
            'attack_strength_diff': home_form.get('goals_per_game', 0) - away_form.get('goals_per_game', 0),
            'defense_strength_diff': away_form.get('conceded_per_game', 0) - home_form.get('conceded_per_game', 0),
            'player_quality_diff': home_players.get('avg_goals_per_match', 0) - away_players.get('avg_goals_per_match', 0),
            
            # Overall team strength (season-long performance)
            'home_overall_strength': home_form.get('form_score', 0.5) * home_form.get('goals_per_game', 1.0),
            'away_overall_strength': away_form.get('form_score', 0.5) * away_form.get('goals_per_game', 1.0),
            'strength_ratio': (home_form.get('form_score', 0.5) * home_form.get('goals_per_game', 1.0)) / 
                            max((away_form.get('form_score', 0.5) * away_form.get('goals_per_game', 1.0)), 0.1),
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
