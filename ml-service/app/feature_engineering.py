"""
Team-Agnostic Feature Engineering
Extracts 31 features for ANY team in ANY match context - no home/away bias.
"""

import psycopg2
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class TeamAgnosticFeatureEngineer:
    """
    Extracts features for team-agnostic prediction.
    Treats all teams equally - venue is just a small feature, not a fundamental split.
    """
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url)
    
    def extract_features_for_team(self, team_id: int, opponent_id: int, 
                                  match_date: str, is_at_venue: bool) -> Dict:
        """
        Extract 31 features for a team attacking an opponent.
        Completely symmetric - no home/away bias.
        
        Args:
            team_id: The attacking team's external_id
            opponent_id: The defending team's external_id
            match_date: Match date for temporal features
            is_at_venue: True if team is at their venue (small boost)
        
        Returns:
            Dict with 31 features
        """
        features = {}
        
        # 1. Team Quality Rating (0-100 based on season performance)
        team_quality = self._get_team_quality_rating(team_id, match_date)
        features['team_quality_rating'] = team_quality
        
        # 2. Opponent Defensive Quality
        opponent_quality = self._get_team_quality_rating(opponent_id, match_date)
        features['opponent_quality_rating'] = opponent_quality
        
        # 3-10. Attacking Team Features (xG, goals, shots)
        team_attack = self._get_team_attacking_stats(team_id, match_date)
        features['team_xg_per_game'] = team_attack.get('xg_per_game', 1.5)
        features['team_goals_per_game'] = team_attack.get('goals_per_game', 1.5)
        features['team_shots_per_game'] = team_attack.get('shots_per_game', 12)
        features['team_striker_xg'] = team_attack.get('top_striker_xg', 0.5)
        features['team_playmaker_assists'] = team_attack.get('playmaker_assists', 3)
        features['team_formation_attack'] = team_attack.get('formation_attack_score', 5)
        features['team_pressing_intensity'] = team_attack.get('pressing_intensity', 5)
        features['team_possession_avg'] = team_attack.get('possession_avg', 50)
        
        # 11-16. Defending Team Features
        opponent_defense = self._get_team_defensive_stats(opponent_id, match_date)
        features['opponent_xg_conceded'] = opponent_defense.get('xg_conceded_per_game', 1.5)
        features['opponent_goals_conceded'] = opponent_defense.get('goals_conceded_per_game', 1.5)
        features['opponent_defensive_rating'] = opponent_defense.get('defensive_rating', 5)
        features['opponent_goalkeeper_save_pct'] = opponent_defense.get('goalkeeper_save_pct', 0.7)
        features['opponent_tackles_per_game'] = opponent_defense.get('tackles_per_game', 15)
        features['opponent_formation_defense'] = opponent_defense.get('formation_defense_score', 5)
        
        # 17-20. Match Context
        features['venue_factor'] = 1.0 if is_at_venue else 0.85  # Small boost for home venue
        features['rest_days'] = self._calculate_rest_days(team_id, match_date)
        features['travel_distance'] = 0 if is_at_venue else self._estimate_travel_distance(team_id, opponent_id)
        features['injury_impact'] = self._calculate_injury_impact(team_id, match_date)
        
        # 21-23. Head-to-Head (team-specific, not position-specific)
        h2h = self._get_head_to_head_stats(team_id, opponent_id, match_date)
        features['h2h_goals_scored_avg'] = h2h.get('goals_scored_avg', 1.5)
        features['h2h_goals_conceded_avg'] = h2h.get('goals_conceded_avg', 1.5)
        features['h2h_win_rate'] = h2h.get('win_rate', 0.5)
        
        # 24-27. Form and Momentum
        form = self._get_team_form(team_id, match_date)
        features['team_form_last_5'] = form.get('form_last_5', 0.5)
        features['team_form_last_10'] = form.get('form_last_10', 0.5)
        features['team_momentum'] = form.get('momentum', 0)
        
        opponent_form = self._get_team_form(opponent_id, match_date)
        features['opponent_form_last_5'] = opponent_form.get('form_last_5', 0.5)
        
        # 28-29. Tactical
        features['coach_win_rate'] = self._get_coach_win_rate(team_id, match_date)
        features['tactical_matchup_score'] = self._calculate_tactical_matchup(team_id, opponent_id, match_date)
        
        # 30-31. Quality Difference (derived features)
        features['quality_difference'] = team_quality - opponent_quality
        features['attack_vs_defense'] = features['team_xg_per_game'] - features['opponent_xg_conceded']
        
        return features
    
    def _get_team_quality_rating(self, team_id: int, before_date: str) -> float:
        """Calculate team quality rating (0-100) based on season performance"""
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                COUNT(*) as total_matches,
                SUM(CASE 
                    WHEN (m.home_team_id = t.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t.id AND m.winner = 'AWAY_TEAM') 
                    THEN 1 ELSE 0 END) as wins,
                AVG(CASE 
                    WHEN m.home_team_id = t.id THEN m.home_score 
                    ELSE m.away_score 
                END) as avg_goals_scored,
                AVG(CASE 
                    WHEN m.home_team_id = t.id THEN m.away_score 
                    ELSE m.home_score 
                END) as avg_goals_conceded
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '365 days')
              AND m.home_score IS NOT NULL
        """
        
        df = pd.read_sql(query, conn, params=(team_id, before_date, before_date))
        conn.close()
        
        if len(df) == 0 or df.iloc[0]['total_matches'] == 0:
            return 50.0  # Default neutral rating
        
        row = df.iloc[0]
        total = row['total_matches']
        
        # Win rate component (0-100)
        win_rate = (row['wins'] / total) * 100 if total > 0 else 50
        
        # Goal difference component (normalized to 0-100)
        goal_diff = (row['avg_goals_scored'] - row['avg_goals_conceded']) if row['avg_goals_scored'] else 0
        goal_score = min(100, max(0, 50 + (goal_diff * 10)))
        
        # Weighted combination: 60% win rate, 40% goal performance
        quality_rating = (win_rate * 0.6) + (goal_score * 0.4)
        
        return round(quality_rating, 2)
    
    def _get_team_attacking_stats(self, team_id: int, before_date: str) -> Dict:
        """Get team's attacking statistics"""
        conn = self.get_db_connection()
        
        # Try to get from team_tactics table first (if populated)
        query_tactics = """
            SELECT xg_per_game, avg_shots_per_game, avg_possession, pressing_intensity
            FROM team_tactics
            WHERE team_id = (SELECT id FROM teams WHERE external_id = %s)
              AND season = '2024'
            LIMIT 1
        """
        
        df_tactics = pd.read_sql(query_tactics, conn, params=(team_id,))
        
        # Fallback to calculating from matches
        query_matches = """
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
        
        df_matches = pd.read_sql(query_matches, conn, params=(team_id, before_date, before_date))
        conn.close()
        
        stats = {
            'xg_per_game': df_tactics.iloc[0]['xg_per_game'] if len(df_tactics) > 0 else 1.5,
            'goals_per_game': df_matches.iloc[0]['goals_per_game'] if len(df_matches) > 0 else 1.5,
            'shots_per_game': df_tactics.iloc[0]['avg_shots_per_game'] if len(df_tactics) > 0 else 12,
            'possession_avg': df_tactics.iloc[0]['avg_possession'] if len(df_tactics) > 0 else 50,
            'pressing_intensity': df_tactics.iloc[0]['pressing_intensity'] if len(df_tactics) > 0 else 5,
            'top_striker_xg': 0.5,  # TODO: Get from player_match_stats_enhanced
            'playmaker_assists': 3,  # TODO: Get from player_match_stats_enhanced
            'formation_attack_score': 5,  # TODO: Calculate from formation
        }
        
        return stats
    
    def _get_team_defensive_stats(self, team_id: int, before_date: str) -> Dict:
        """Get team's defensive statistics"""
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                AVG(CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END) as goals_conceded_per_game,
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
        conn.close()
        
        stats = {
            'xg_conceded_per_game': 1.5,  # TODO: Get from team_tactics
            'goals_conceded_per_game': df.iloc[0]['goals_conceded_per_game'] if len(df) > 0 else 1.5,
            'defensive_rating': 5,  # TODO: Calculate from team_tactics
            'goalkeeper_save_pct': 0.7,  # TODO: Get from player stats
            'tackles_per_game': 15,  # TODO: Get from team_tactics
            'formation_defense_score': 5,  # TODO: Calculate from formation
        }
        
        return stats
    
    def _calculate_rest_days(self, team_id: int, match_date: str) -> int:
        """Calculate days since last match"""
        conn = self.get_db_connection()
        
        query = """
            SELECT MAX(m.utc_date) as last_match_date
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
        """
        
        df = pd.read_sql(query, conn, params=(team_id, match_date))
        conn.close()
        
        if len(df) > 0 and df.iloc[0]['last_match_date']:
            last_match = pd.to_datetime(df.iloc[0]['last_match_date'])
            current_match = pd.to_datetime(match_date)
            rest_days = (current_match - last_match).days
            return min(rest_days, 14)  # Cap at 14 days
        
        return 7  # Default
    
    def _estimate_travel_distance(self, team_id: int, opponent_id: int) -> float:
        """Estimate travel distance (simplified - returns 0 for same country, 200 for different)"""
        # TODO: Implement proper distance calculation based on team locations
        return 200.0  # Default assumption for away matches
    
    def _calculate_injury_impact(self, team_id: int, match_date: str) -> float:
        """Calculate impact of injuries on team strength"""
        conn = self.get_db_connection()
        
        query = """
            SELECT COUNT(*) as injured_count
            FROM player_availability pa
            JOIN players p ON pa.player_id = p.id
            JOIN teams t ON p.team_id = t.id
            WHERE t.external_id = %s
              AND pa.unavailable_from <= %s
              AND (pa.unavailable_until IS NULL OR pa.unavailable_until >= %s)
              AND pa.reason IN ('injury', 'suspension')
        """
        
        df = pd.read_sql(query, conn, params=(team_id, match_date, match_date))
        conn.close()
        
        injured_count = df.iloc[0]['injured_count'] if len(df) > 0 else 0
        
        # Each injury reduces strength by 0.05, cap at -0.3
        return -min(0.3, injured_count * 0.05)
    
    def _get_head_to_head_stats(self, team_id: int, opponent_id: int, before_date: str) -> Dict:
        """Get head-to-head statistics between two teams"""
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                AVG(CASE WHEN m.home_team_id = t1.id THEN m.home_score ELSE m.away_score END) as goals_scored_avg,
                AVG(CASE WHEN m.home_team_id = t1.id THEN m.away_score ELSE m.home_score END) as goals_conceded_avg,
                SUM(CASE 
                    WHEN (m.home_team_id = t1.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t1.id AND m.winner = 'AWAY_TEAM') 
                    THEN 1 ELSE 0 END)::float / COUNT(*)::float as win_rate
            FROM teams t1
            JOIN teams t2 ON t2.external_id = %s
            JOIN matches m ON (
                (m.home_team_id = t1.id AND m.away_team_id = t2.id) OR
                (m.away_team_id = t1.id AND m.home_team_id = t2.id)
            )
            WHERE t1.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
              AND m.utc_date > (DATE %s - INTERVAL '730 days')
        """
        
        df = pd.read_sql(query, conn, params=(opponent_id, team_id, before_date, before_date))
        conn.close()
        
        if len(df) > 0 and df.iloc[0]['goals_scored_avg'] is not None:
            return {
                'goals_scored_avg': float(df.iloc[0]['goals_scored_avg']),
                'goals_conceded_avg': float(df.iloc[0]['goals_conceded_avg']),
                'win_rate': float(df.iloc[0]['win_rate']) if df.iloc[0]['win_rate'] else 0.5
            }
        
        return {'goals_scored_avg': 1.5, 'goals_conceded_avg': 1.5, 'win_rate': 0.5}
    
    def _get_team_form(self, team_id: int, before_date: str) -> Dict:
        """Get team's recent form"""
        conn = self.get_db_connection()
        
        # Last 5 matches
        query_5 = """
            SELECT 
                SUM(CASE 
                    WHEN (m.home_team_id = t.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t.id AND m.winner = 'AWAY_TEAM') 
                    THEN 3
                    WHEN m.winner = 'DRAW' THEN 1
                    ELSE 0 END)::float / (COUNT(*) * 3)::float as form_score
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
            ORDER BY m.utc_date DESC
            LIMIT 5
        """
        
        df_5 = pd.read_sql(query_5, conn, params=(team_id, before_date))
        
        # Last 10 matches
        query_10 = """
            SELECT 
                SUM(CASE 
                    WHEN (m.home_team_id = t.id AND m.winner = 'HOME_TEAM') OR 
                         (m.away_team_id = t.id AND m.winner = 'AWAY_TEAM') 
                    THEN 3
                    WHEN m.winner = 'DRAW' THEN 1
                    ELSE 0 END)::float / (COUNT(*) * 3)::float as form_score
            FROM teams t
            JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
            WHERE t.external_id = %s
              AND m.status = 'FINISHED'
              AND m.utc_date < %s
            ORDER BY m.utc_date DESC
            LIMIT 10
        """
        
        df_10 = pd.read_sql(query_10, conn, params=(team_id, before_date))
        conn.close()
        
        form_5 = df_5.iloc[0]['form_score'] if len(df_5) > 0 and df_5.iloc[0]['form_score'] else 0.5
        form_10 = df_10.iloc[0]['form_score'] if len(df_10) > 0 and df_10.iloc[0]['form_score'] else 0.5
        
        # Momentum: difference between recent and medium-term form
        momentum = form_5 - form_10
        
        return {
            'form_last_5': float(form_5),
            'form_last_10': float(form_10),
            'momentum': float(momentum)
        }
    
    def _get_coach_win_rate(self, team_id: int, before_date: str) -> float:
        """Get coach's win rate"""
        conn = self.get_db_connection()
        
        query = """
            SELECT 
                COALESCE(tc.wins::float / NULLIF(tc.matches_managed, 0)::float, 0.5) as win_rate
            FROM team_coaches tc
            JOIN teams t ON tc.team_id = t.id
            WHERE t.external_id = %s
              AND tc.season = '2024'
            LIMIT 1
        """
        
        df = pd.read_sql(query, conn, params=(team_id,))
        conn.close()
        
        if len(df) > 0:
            return float(df.iloc[0]['win_rate'])
        
        return 0.5  # Default
    
    def _calculate_tactical_matchup(self, team_id: int, opponent_id: int, before_date: str) -> float:
        """Calculate tactical matchup score (simplified)"""
        # TODO: Implement formation-based tactical analysis
        # For now, return neutral score
        return 5.0
    
    def extract_match_features(self, team_a_id: int, team_b_id: int, 
                               match_date: str) -> Tuple[Dict, Dict]:
        """
        Extract features for both teams in a match.
        Returns: (team_a_features, team_b_features)
        """
        # Determine which team is at their venue (if applicable)
        # For now, assume first team is at venue
        team_a_features = self.extract_features_for_team(
            team_id=team_a_id,
            opponent_id=team_b_id,
            match_date=match_date,
            is_at_venue=True
        )
        
        team_b_features = self.extract_features_for_team(
            team_id=team_b_id,
            opponent_id=team_a_id,
            match_date=match_date,
            is_at_venue=False
        )
        
        return team_a_features, team_b_features


# Example usage
if __name__ == "__main__":
    engineer = TeamAgnosticFeatureEngineer()
    
    # Test: Extract features for Man City vs Burnley
    # Man City external_id: 65, Burnley: 73 (example IDs)
    team_a_features, team_b_features = engineer.extract_match_features(
        team_a_id=65,
        team_b_id=73,
        match_date='2025-01-15'
    )
    
    print("Team A Features (31 total):")
    for key, value in team_a_features.items():
        print(f"  {key}: {value}")
    
    print(f"\nTotal features extracted: {len(team_a_features)}")
