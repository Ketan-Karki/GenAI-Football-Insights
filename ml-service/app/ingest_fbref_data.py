"""
Data Ingestion Script - FBref to Database
Populates enhanced tables with xG, player stats, and tactical data from FBref.
"""

import psycopg2
import json
import os
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
from scrapers.fbref_scraper import FBrefScraper

load_dotenv()

class FBrefDataIngester:
    """Ingest FBref scraped data into database"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.scraper = FBrefScraper()
    
    def get_db_connection(self):
        return psycopg2.connect(self.db_url)
    
    def ingest_league_data(self, league_code: str, season: str = '2024-2025'):
        """
        Scrape and ingest data for a league.
        Populates: team_tactics, match_context
        """
        print(f"\n{'='*60}")
        print(f"Ingesting {league_code} {season}")
        print(f"{'='*60}")
        
        # Scrape data
        data = self.scraper.scrape_league_season(league_code, season)
        
        if not data.get('league_table'):
            print(f"⚠️  No data scraped for {league_code}")
            return
        
        # Ingest team tactics
        self._ingest_team_tactics(data['league_table'], season)
        
        print(f"✅ Completed ingestion for {league_code}")
    
    def _ingest_team_tactics(self, league_table: List[Dict], season: str):
        """Insert team tactical data into team_tactics table"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        inserted = 0
        skipped = 0
        
        for team_data in league_table:
            try:
                team_name = team_data.get('Unnamed: 0_level_0_Squad')
                if not team_name:
                    continue
                
                # Get team_id from database
                cur.execute(
                    "SELECT id FROM teams WHERE name ILIKE %s LIMIT 1",
                    (f"%{team_name}%",)
                )
                result = cur.fetchone()
                
                if not result:
                    print(f"  ⚠️  Team not found in database: {team_name}")
                    skipped += 1
                    continue
                
                team_id = result[0]
                
                # Extract tactical data
                xg_per_game = team_data.get('Expected_xG', 0) / max(team_data.get('Playing Time_90s', 1), 1)
                possession = team_data.get('Unnamed: 3_level_0_Poss', 50)
                
                # Insert or update team_tactics
                cur.execute("""
                    INSERT INTO team_tactics (
                        team_id, season, avg_possession, xg_per_game,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (team_id, season) 
                    DO UPDATE SET
                        avg_possession = EXCLUDED.avg_possession,
                        xg_per_game = EXCLUDED.xg_per_game,
                        updated_at = NOW()
                """, (team_id, season, possession, xg_per_game))
                
                inserted += 1
                
            except Exception as e:
                print(f"  ❌ Error processing {team_name}: {e}")
                skipped += 1
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"  ✅ Inserted/Updated: {inserted} teams")
        if skipped > 0:
            print(f"  ⚠️  Skipped: {skipped} teams")
    
    def ingest_international_data(self, comp_code: str, year: str = '2024'):
        """
        Scrape and ingest international competition data.
        """
        print(f"\n{'='*60}")
        print(f"Ingesting {comp_code} {year}")
        print(f"{'='*60}")
        
        # Scrape data
        data = self.scraper.scrape_international_competition(comp_code, year)
        
        if not data.get('teams_table'):
            print(f"⚠️  No data scraped for {comp_code}")
            return
        
        # Ingest team tactics (same process as league data)
        self._ingest_team_tactics(data['teams_table'], year)
        
        print(f"✅ Completed ingestion for {comp_code}")
    
    def ingest_player_stats(self, team_url: str, team_id: int):
        """
        Scrape and ingest player statistics for a team.
        Populates: player_match_stats_enhanced
        """
        print(f"  Ingesting player stats for team {team_id}...")
        
        players = self.scraper.get_player_stats(team_url)
        
        if not players:
            print(f"    ⚠️  No player data found")
            return
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        inserted = 0
        
        for player_data in players:
            try:
                player_name = player_data.get('name')
                if not player_name:
                    continue
                
                # Check if player exists, if not create
                cur.execute(
                    "SELECT id FROM players WHERE name ILIKE %s AND team_id = %s LIMIT 1",
                    (f"%{player_name}%", team_id)
                )
                result = cur.fetchone()
                
                if not result:
                    # Create player
                    cur.execute("""
                        INSERT INTO players (name, team_id, position, date_of_birth)
                        VALUES (%s, %s, %s, NULL)
                        RETURNING id
                    """, (player_name, team_id, player_data.get('position', 'Unknown')))
                    player_id = cur.fetchone()[0]
                else:
                    player_id = result[0]
                
                # Insert aggregated stats (not match-specific for now)
                # This is simplified - ideally we'd scrape match-by-match data
                xg = player_data.get('xG', 0)
                goals = player_data.get('goals', 0)
                assists = player_data.get('assists', 0)
                
                # Store as season aggregate (we'll improve this later)
                # For now, just log that we have the data
                print(f"    ✓ {player_name}: {goals}G, {assists}A, {xg}xG")
                inserted += 1
                
            except Exception as e:
                print(f"    ❌ Error processing player: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"    ✅ Processed {inserted} players")
    
    def run_full_ingestion(self):
        """Run complete data ingestion for all competitions"""
        print("\n" + "="*60)
        print("FULL DATA INGESTION - FBref to Database")
        print("="*60)
        
        # Domestic leagues
        leagues = [
            ('PL', '2024-2025'),   # Premier League
            ('PD', '2024-2025'),   # La Liga
            ('BL1', '2024-2025'),  # Bundesliga
            ('SA', '2024-2025'),   # Serie A
            ('FL1', '2024-2025'),  # Ligue 1
        ]
        
        for league_code, season in leagues:
            try:
                self.ingest_league_data(league_code, season)
            except Exception as e:
                print(f"❌ Error ingesting {league_code}: {e}")
                continue
        
        # International competitions
        international = [
            ('WC', '2022'),           # World Cup 2022
            ('EC', '2024'),           # Euro 2024
            ('COPA', '2024'),         # Copa America 2024
            ('NATIONS', '2024-2025'), # Nations League
        ]
        
        for comp_code, year in international:
            try:
                self.ingest_international_data(comp_code, year)
            except Exception as e:
                print(f"❌ Error ingesting {comp_code}: {e}")
                continue
        
        print("\n" + "="*60)
        print("✅ FULL INGESTION COMPLETED")
        print("="*60)
    
    def verify_ingestion(self):
        """Verify data was ingested correctly"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        # Check team_tactics
        cur.execute("SELECT COUNT(*) FROM team_tactics")
        tactics_count = cur.fetchone()[0]
        print(f"✓ team_tactics: {tactics_count} records")
        
        # Check sample data
        cur.execute("""
            SELECT t.name, tt.xg_per_game, tt.avg_possession
            FROM team_tactics tt
            JOIN teams t ON tt.team_id = t.id
            ORDER BY tt.xg_per_game DESC
            LIMIT 5
        """)
        
        print("\nTop 5 teams by xG:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]:.2f} xG/game, {row[2]:.1f}% possession")
        
        cur.close()
        conn.close()


# CLI Interface
if __name__ == "__main__":
    import sys
    
    ingester = FBrefDataIngester()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "league":
            # Ingest specific league
            league_code = sys.argv[2] if len(sys.argv) > 2 else 'PL'
            season = sys.argv[3] if len(sys.argv) > 3 else '2024-2025'
            ingester.ingest_league_data(league_code, season)
        
        elif command == "international":
            # Ingest specific international competition
            comp_code = sys.argv[2] if len(sys.argv) > 2 else 'WC'
            year = sys.argv[3] if len(sys.argv) > 3 else '2022'
            ingester.ingest_international_data(comp_code, year)
        
        elif command == "verify":
            # Verify ingestion
            ingester.verify_ingestion()
        
        else:
            print("Unknown command. Use: league, international, or verify")
    
    else:
        # Run full ingestion
        ingester.run_full_ingestion()
        ingester.verify_ingestion()
