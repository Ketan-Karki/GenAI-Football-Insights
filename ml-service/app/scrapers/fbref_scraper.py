"""
FBref.com scraper for xG, player stats, and tactical data.
Free alternative to paid APIs.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Dict, List, Optional
import re
from datetime import datetime

class FBrefScraper:
    """Scrape football data from FBref.com"""
    
    BASE_URL = "https://fbref.com"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    # League and Competition URLs on FBref
    LEAGUE_URLS = {
        # Domestic Leagues
        'PL': '/en/comps/9/Premier-League-Stats',
        'PD': '/en/comps/12/La-Liga-Stats',
        'BL1': '/en/comps/20/Bundesliga-Stats',
        'SA': '/en/comps/11/Serie-A-Stats',
        'FL1': '/en/comps/13/Ligue-1-Stats',
        
        # Club Competitions
        'CL': '/en/comps/8/Champions-League-Stats',
        'EL': '/en/comps/19/Europa-League-Stats',
        
        # International Competitions (for World Cup predictions)
        'WC': '/en/comps/1/World-Cup-Stats',  # World Cup 2022
        'EC': '/en/comps/676/European-Championship-Stats',  # Euro 2024
        'COPA': '/en/comps/685/Copa-America-Stats',  # Copa America 2024
        'NATIONS': '/en/comps/683/UEFA-Nations-League-Stats',  # Nations League 2024-25
        
        # World Cup Qualifiers
        'WCQ_UEFA': '/en/comps/676/European-Championship-Qualifying-Stats',
        'WCQ_CONMEBOL': '/en/comps/685/CONMEBOL-World-Cup-Qualifying-Stats',
        'WCQ_AFC': '/en/comps/1237/AFC-World-Cup-Qualifying-Stats',
        'WCQ_CAF': '/en/comps/1238/CAF-World-Cup-Qualifying-Stats',
        'WCQ_CONCACAF': '/en/comps/1239/CONCACAF-World-Cup-Qualifying-Stats',
        
        # Continental Championships
        'AFCON': '/en/comps/690/Africa-Cup-of-Nations-Stats',
        'GOLD_CUP': '/en/comps/688/Gold-Cup-Stats',
        'ASIAN_CUP': '/en/comps/691/Asian-Cup-Stats',
        
        # Friendlies (if available)
        'FRIENDLIES': '/en/comps/218/Friendlies-Stats',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            time.sleep(3)  # Be respectful - 3 second delay
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def get_league_table_with_xg(self, league_code: str, season: str = '2024-2025') -> pd.DataFrame:
        """
        Get league table with xG data.
        Returns: DataFrame with team stats including xG, xGA, possession, etc.
        """
        league_url = self.LEAGUE_URLS.get(league_code)
        if not league_url:
            print(f"Unknown league: {league_code}")
            return pd.DataFrame()
        
        url = f"{self.BASE_URL}{league_url}"
        print(f"Fetching: {url}")
        soup = self._get_page(url)
        if not soup:
            return pd.DataFrame()
        
        # Try multiple table IDs that FBref might use
        table_ids = [
            'stats_squads_standard',
            'stats_squads_standard_for',
            'results',
            'stats_standard'
        ]
        
        table = None
        for table_id in table_ids:
            table = soup.find('table', {'id': table_id})
            if table:
                print(f"Found table with ID: {table_id}")
                break
        
        # If no table found by ID, try finding any table with class 'stats_table'
        if not table:
            table = soup.find('table', {'class': 'stats_table'})
            if table:
                print("Found table by class 'stats_table'")
        
        if not table:
            print("Could not find stats table")
            print(f"Available tables: {[t.get('id') for t in soup.find_all('table') if t.get('id')]}")
            return pd.DataFrame()
        
        try:
            # Parse table
            df = pd.read_html(str(table))[0]
            
            # Clean column names (FBref has multi-level columns)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            print(f"Successfully parsed table with {len(df)} rows")
            return df
        except Exception as e:
            print(f"Error parsing table: {e}")
            return pd.DataFrame()
    
    def get_team_xg_data(self, team_url: str) -> Dict:
        """
        Get detailed xG data for a specific team.
        Returns: Dict with xG per game, xGA, shooting stats, etc.
        """
        soup = self._get_page(f"{self.BASE_URL}{team_url}")
        if not soup:
            return {}
        
        xg_data = {}
        
        # Find shooting table
        shooting_table = soup.find('table', {'id': 'stats_shooting'})
        if shooting_table:
            df = pd.read_html(str(shooting_table))[0]
            
            # Extract xG metrics
            if 'xG' in df.columns:
                xg_data['xG_per_game'] = df['xG'].mean()
            if 'xG_per_shot' in df.columns:
                xg_data['xG_per_shot'] = df['xG_per_shot'].mean()
        
        return xg_data
    
    def get_player_stats(self, team_url: str, season: str = '2024-2025') -> List[Dict]:
        """
        Get player statistics for a team including xG.
        Returns: List of player stat dictionaries
        """
        soup = self._get_page(f"{self.BASE_URL}{team_url}")
        if not soup:
            return []
        
        players = []
        
        # Find standard stats table
        stats_table = soup.find('table', {'id': 'stats_standard'})
        if stats_table:
            df = pd.read_html(str(stats_table))[0]
            
            # Clean columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            # Extract player data
            for _, row in df.iterrows():
                try:
                    player = {
                        'name': row.get('Player', ''),
                        'position': row.get('Pos', ''),
                        'age': row.get('Age', 0),
                        'matches_played': row.get('MP', 0),
                        'starts': row.get('Starts', 0),
                        'minutes': row.get('Min', 0),
                        'goals': row.get('Gls', 0),
                        'assists': row.get('Ast', 0),
                        'xG': row.get('xG', 0.0),
                        'xAG': row.get('xAG', 0.0),  # Expected assisted goals
                    }
                    players.append(player)
                except Exception as e:
                    continue
        
        return players
    
    def get_match_xg_data(self, match_url: str) -> Dict:
        """
        Get xG data for a specific match.
        Returns: Dict with team xG, shots, possession, etc.
        """
        soup = self._get_page(f"{self.BASE_URL}{match_url}")
        if not soup:
            return {}
        
        match_data = {}
        
        # Find scorebox with basic match info
        scorebox = soup.find('div', {'class': 'scorebox'})
        if scorebox:
            # Extract team names and scores
            teams = scorebox.find_all('div', {'itemprop': 'performer'})
            if len(teams) >= 2:
                match_data['team_a'] = teams[0].find('a').text.strip()
                match_data['team_b'] = teams[1].find('a').text.strip()
        
        # Find shot data table (includes xG)
        shot_table = soup.find('table', {'id': 'shots_all'})
        if shot_table:
            df = pd.read_html(str(shot_table))[0]
            
            # Calculate xG for each team
            if 'xG' in df.columns and 'Squad' in df.columns:
                team_a_xg = df[df['Squad'] == match_data.get('team_a')]['xG'].sum()
                team_b_xg = df[df['Squad'] == match_data.get('team_b')]['xG'].sum()
                
                match_data['team_a_xg'] = round(team_a_xg, 2)
                match_data['team_b_xg'] = round(team_b_xg, 2)
        
        # Find possession data
        possession_div = soup.find('div', {'id': 'team_stats'})
        if possession_div:
            poss_text = possession_div.text
            poss_match = re.search(r'Possession.*?(\d+)%.*?(\d+)%', poss_text)
            if poss_match:
                match_data['team_a_possession'] = int(poss_match.group(1))
                match_data['team_b_possession'] = int(poss_match.group(2))
        
        return match_data
    
    def get_team_formation_data(self, team_url: str) -> Dict:
        """
        Get team's typical formation and tactical data.
        Returns: Dict with formation, pressing stats, etc.
        """
        soup = self._get_page(f"{self.BASE_URL}{team_url}")
        if not soup:
            return {}
        
        tactical_data = {}
        
        # Find possession table
        poss_table = soup.find('table', {'id': 'stats_possession'})
        if poss_table:
            df = pd.read_html(str(poss_table))[0]
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            # Extract tactical metrics
            tactical_data['avg_possession'] = df.get('Possession_Poss', pd.Series([0])).mean()
            tactical_data['touches_att_3rd'] = df.get('Touches_Att 3rd', pd.Series([0])).mean()
            tactical_data['progressive_passes'] = df.get('Carries_PrgC', pd.Series([0])).mean()
        
        # Find defensive actions table
        def_table = soup.find('table', {'id': 'stats_defense'})
        if def_table:
            df = pd.read_html(str(def_table))[0]
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            tactical_data['tackles_per_game'] = df.get('Tackles_Tkl', pd.Series([0])).mean()
            tactical_data['pressures_per_game'] = df.get('Pressures_Press', pd.Series([0])).mean()
            tactical_data['interceptions_per_game'] = df.get('Int', pd.Series([0])).mean()
        
        return tactical_data
    
    def scrape_league_season(self, league_code: str, season: str = '2024-2025') -> Dict:
        """
        Scrape all data for a league season.
        Returns: Dict with teams, players, matches, and tactical data
        """
        print(f"Scraping {league_code} {season}...")
        
        data = {
            'league': league_code,
            'season': season,
            'teams': [],
            'scraped_at': datetime.now().isoformat()
        }
        
        # Get league table with xG
        league_table = self.get_league_table_with_xg(league_code, season)
        if not league_table.empty:
            data['league_table'] = league_table.to_dict('records')
        
        print(f"✅ Scraped {len(data.get('league_table', []))} teams")
        
        return data
    
    def scrape_international_competition(self, comp_code: str, year: str = '2024') -> Dict:
        """
        Scrape international competition data (World Cup, Euro, Copa America, etc.)
        Returns: Dict with national teams, players, matches, and stats
        """
        print(f"Scraping international competition: {comp_code} {year}...")
        
        data = {
            'competition': comp_code,
            'year': year,
            'teams': [],
            'is_international': True,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Get competition table/standings
        comp_table = self.get_league_table_with_xg(comp_code, year)
        if not comp_table.empty:
            data['teams_table'] = comp_table.to_dict('records')
            print(f"✅ Scraped {len(data['teams_table'])} national teams")
        
        return data
    
    def get_national_team_stats(self, team_name: str, competition: str = 'all') -> Dict:
        """
        Get statistics for a national team across competitions.
        Useful for World Cup predictions.
        """
        print(f"Getting stats for {team_name}...")
        
        stats = {
            'team_name': team_name,
            'competitions': [],
            'overall_stats': {}
        }
        
        # This would aggregate stats from multiple competitions
        # Nations League, WC Qualifiers, Friendlies, etc.
        
        return stats


# Example usage
if __name__ == "__main__":
    scraper = FBrefScraper()
    
    # Test: Get Premier League data
    pl_data = scraper.scrape_league_season('PL', '2024-2025')
    print(f"Scraped {len(pl_data.get('league_table', []))} Premier League teams")
    
    # Test: Get international competition data
    print("\n" + "="*60)
    print("Scraping International Competitions for World Cup Predictions")
    print("="*60)
    
    international_data = {}
    
    # World Cup 2022
    wc_data = scraper.scrape_international_competition('WC', '2022')
    international_data['world_cup_2022'] = wc_data
    
    # Euro 2024
    euro_data = scraper.scrape_international_competition('EC', '2024')
    international_data['euro_2024'] = euro_data
    
    # Copa America 2024
    copa_data = scraper.scrape_international_competition('COPA', '2024')
    international_data['copa_america_2024'] = copa_data
    
    # Nations League 2024-25
    nations_data = scraper.scrape_international_competition('NATIONS', '2024-2025')
    international_data['nations_league_2024'] = nations_data
    
    # AFCON
    afcon_data = scraper.scrape_international_competition('AFCON', '2024')
    international_data['afcon_2024'] = afcon_data
    
    # Save to file
    import json
    
    with open('fbref_domestic_data.json', 'w') as f:
        json.dump(pl_data, f, indent=2)
    
    with open('fbref_international_data.json', 'w') as f:
        json.dump(international_data, f, indent=2)
    
    print("\n✅ Domestic data saved to fbref_domestic_data.json")
    print("✅ International data saved to fbref_international_data.json")
    print(f"\nTotal international competitions scraped: {len(international_data)}")
