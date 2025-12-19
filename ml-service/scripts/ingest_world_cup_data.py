"""
Ingest FIFA World Cup historical data from the Fjelstul World Cup Database
This provides historical match data for international teams to enable predictions
"""

import requests
import pandas as pd
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# GitHub raw URLs for the CSV data
BASE_URL = "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/"

DATASETS = {
    'matches': 'matches.csv',
    'teams': 'teams.csv',
    'team_appearances': 'team_appearances.csv',
    'tournaments': 'tournaments.csv',
}

def download_csv(filename):
    """Download CSV from GitHub"""
    url = BASE_URL + filename
    print(f"Downloading {filename}...")
    response = requests.get(url)
    response.raise_for_status()
    return pd.read_csv(url)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def ingest_international_teams(teams_df):
    """Ingest international teams into the teams table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\nIngesting {len(teams_df)} international teams...")
    
    for _, team in teams_df.iterrows():
        # Check if team exists
        cursor.execute("SELECT id FROM teams WHERE name = %s", (team['team_name'],))
        existing = cursor.fetchone()
        
        if not existing:
            # Insert new team
            cursor.execute("""
                INSERT INTO teams (external_id, name, short_name, tla, crest, area_name, area_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_id) DO NOTHING
            """, (
                team['team_id'],
                team['team_name'],
                team['team_name'][:30],  # Short name
                team['team_code'],
                '',  # No crest URL
                team['team_name'],  # Use team name as area
                team['team_code']
            ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Ingested international teams")

def ingest_world_cup_matches(matches_df, team_appearances_df):
    """Ingest World Cup matches with scores"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\nIngesting {len(matches_df)} World Cup matches...")
    
    # Merge team appearances to get scores
    matches_with_scores = matches_df.merge(
        team_appearances_df[team_appearances_df['home_team'] == True][['match_id', 'goals_for', 'goals_against']],
        on='match_id',
        how='left'
    )
    
    ingested = 0
    for _, match in matches_with_scores.iterrows():
        try:
            # Get team IDs from database
            cursor.execute("SELECT id FROM teams WHERE external_id = %s", (match['home_team_id'],))
            home_team = cursor.fetchone()
            
            cursor.execute("SELECT id FROM teams WHERE external_id = %s", (match['away_team_id'],))
            away_team = cursor.fetchone()
            
            if not home_team or not away_team:
                continue
            
            # Determine winner
            if pd.notna(match['goals_for']) and pd.notna(match['goals_against']):
                home_score = int(match['goals_for'])
                away_score = int(match['goals_against'])
                
                if home_score > away_score:
                    winner = 'HOME_TEAM'
                elif away_score > home_score:
                    winner = 'AWAY_TEAM'
                else:
                    winner = 'DRAW'
            else:
                home_score = away_score = None
                winner = None
            
            # Convert date
            match_date = pd.to_datetime(match['match_date']).strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert match
            cursor.execute("""
                INSERT INTO matches (
                    external_id, competition_id, season_id, utc_date, status,
                    matchday, stage, home_team_id, away_team_id,
                    home_score, away_score, winner
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (external_id) DO UPDATE SET
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    winner = EXCLUDED.winner,
                    status = 'FINISHED'
            """, (
                match['match_id'],
                2000,  # World Cup competition ID
                match['tournament_id'],
                match_date,
                'FINISHED',
                1,  # Matchday
                match['stage_name'],
                home_team[0],
                away_team[0],
                home_score,
                away_score,
                winner
            ))
            ingested += 1
            
        except Exception as e:
            print(f"Error ingesting match {match['match_id']}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Ingested {ingested} World Cup matches")

def calculate_team_stats():
    """Calculate basic stats for international teams based on historical matches"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\nCalculating team statistics...")
    
    # Get all international teams
    cursor.execute("""
        SELECT DISTINCT t.id, t.external_id, t.name
        FROM teams t
        WHERE t.external_id < 10000  -- International teams have lower IDs
    """)
    teams = cursor.fetchall()
    
    for team_id, external_id, team_name in teams:
        # Calculate stats from historical matches
        cursor.execute("""
            SELECT 
                COUNT(*) as matches_played,
                AVG(CASE WHEN home_team_id = %s THEN home_score ELSE away_score END) as goals_scored,
                AVG(CASE WHEN home_team_id = %s THEN away_score ELSE home_score END) as goals_conceded,
                SUM(CASE 
                    WHEN (home_team_id = %s AND winner = 'HOME_TEAM') OR 
                         (away_team_id = %s AND winner = 'AWAY_TEAM') 
                    THEN 1 ELSE 0 
                END)::float / COUNT(*)::float as win_rate
            FROM matches
            WHERE (home_team_id = %s OR away_team_id = %s)
              AND status = 'FINISHED'
              AND home_score IS NOT NULL
        """, (team_id, team_id, team_id, team_id, team_id, team_id))
        
        stats = cursor.fetchone()
        if stats and stats[0] > 0:
            matches_played, goals_scored, goals_conceded, win_rate = stats
            print(f"  {team_name}: {matches_played} matches, {goals_scored:.2f} goals/game, {win_rate:.2%} win rate")
    
    cursor.close()
    conn.close()
    print("✅ Statistics calculated")

def main():
    print("="*60)
    print("INGESTING FIFA WORLD CUP HISTORICAL DATA")
    print("="*60)
    
    try:
        # Download datasets
        teams_df = download_csv(DATASETS['teams'])
        matches_df = download_csv(DATASETS['matches'])
        team_appearances_df = download_csv(DATASETS['team_appearances'])
        tournaments_df = download_csv(DATASETS['tournaments'])
        
        print(f"\n📊 Downloaded:")
        print(f"  - {len(teams_df)} teams")
        print(f"  - {len(matches_df)} matches")
        print(f"  - {len(tournaments_df)} tournaments")
        
        # Ingest data
        ingest_international_teams(teams_df)
        ingest_world_cup_matches(matches_df, team_appearances_df)
        calculate_team_stats()
        
        print("\n" + "="*60)
        print("✅ WORLD CUP DATA INGESTION COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
