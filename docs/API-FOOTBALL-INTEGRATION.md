# API-Football Integration Guide

## Overview

Successfully integrated API-Football for player lineup and statistics data. This provides real player data for the "Key Players" feature in Ball Knowledge insights.

## Setup

### 1. API Key Configuration

Added to `.env`:

```bash
API_FOOTBALL_KEY=ae46126b9ccdabd7b348865d33e61702
API_FOOTBALL_BASE_URL=https://v3.football.api-sports.io
```

### 2. Free Tier Limits

- **100 requests per day**
- Resets daily
- Includes all endpoints we need:
  - ✅ Lineups
  - ✅ Events (goals/assists)
  - ✅ Player stats
  - ✅ Fixtures

## Implementation

### Architecture

**Dual-API Strategy:**

- **football-data.org**: Matches, standings, competitions (primary data source)
- **API-Football**: Player lineups, formations, match events (player data only)

### New Components

1. **`pkg/apifootball/client.go`**

   - HTTP client with API key authentication
   - Methods: `GetFixtureLineups()`, `GetFixtureEvents()`, `GetPlayerStats()`

2. **`pkg/apifootball/models.go`**

   - Data models for API-Football responses
   - Structures: `FixtureLineupsResponse`, `FixtureEvent`, `PlayerStatsResponse`

3. **`pkg/apifootball/mapper.go`**

   - Maps between football-data.org match IDs and API-Football fixture IDs
   - Searches by team names and match date
   - Caches mappings in `match_fixture_mappings` table

4. **`cmd/player_ingest/main.go`**
   - Ingestion command using API-Football
   - Fetches lineups and events for finished matches
   - Extracts goals/assists from events
   - Populates: `players`, `match_lineups`, `match_lineup_players`, `player_match_stats`

## Usage

### Running Player Ingestion

```bash
cd backend
make player-ingest
```

**What it does:**

1. Queries recent finished matches from database
2. Finds corresponding API-Football fixture IDs
3. Fetches lineups (formations, starters, substitutes)
4. Fetches match events (goals, assists, cards)
5. Stores player data and stats in database

**Rate limiting:**

- Processes 5 matches per run (~15 requests)
- Can run ~6 times per day within free tier
- Recommendation: Run once daily via cron

### Testing the Integration

```bash
# Test API connectivity
./test_api_football.sh

# Test full ingestion flow
go run cmd/test_player_ingest/main.go
```

## Data Flow

```
football-data.org Match
         ↓
   Match in DB (with team names, date)
         ↓
   Mapper finds API-Football fixture ID
         ↓
   API-Football: Get lineups + events
         ↓
   Extract: Players, formations, goals, assists
         ↓
   Store in DB: players, match_lineups, player_match_stats
         ↓
   Backend API: GetKeyPlayers()
         ↓
   Frontend: Display in Ball Knowledge
```

## Database Schema

### match_fixture_mappings

Maps between the two APIs:

```sql
CREATE TABLE match_fixture_mappings (
    id SERIAL PRIMARY KEY,
    football_data_match_id INTEGER UNIQUE NOT NULL,
    api_football_fixture_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Response Examples

### Lineups Endpoint

```bash
curl -H "x-apisports-key: YOUR_KEY" \
  "https://v3.football.api-sports.io/fixtures/lineups?fixture=1035098"
```

Returns:

- Team info (name, logo, colors)
- Formation (e.g., "4-2-3-1")
- StartXI: 11 players with positions, numbers
- Substitutes: Bench players
- Coach info

### Events Endpoint

```bash
curl -H "x-apisports-key: YOUR_KEY" \
  "https://v3.football.api-sports.io/fixtures/events?fixture=1035098"
```

Returns:

- Goals (with scorer and assist)
- Cards (yellow/red)
- Substitutions
- VAR decisions
- Time of each event

## Key Features

### 1. Automatic Fixture Mapping

- Searches API-Football by team names + date
- Caches mapping to avoid repeated searches
- Handles team name variations (normalization)

### 2. Goals & Assists Extraction

- Parses match events for goal scorers
- Identifies assist providers
- Stores in `player_match_stats` table
- Powers "Key Players" display

### 3. Formation Data

- Stores tactical formations (e.g., "4-3-3")
- Available for future tactical analysis
- Displayed in lineup context

### 4. Player Positions

- Goalkeeper (G)
- Defender (D)
- Midfielder (M)
- Attacker (F)
- Stored with each player in lineup

## Frontend Integration

No changes needed! The existing implementation already works:

1. **Backend**: `GetKeyPlayers()` queries `player_match_stats`
2. **API**: `/api/v1/predictions/:matchId` includes `keyPlayers`
3. **Frontend**: `match-card.tsx` displays in Ball Knowledge panel

## Monitoring API Usage

Check remaining requests:

```bash
curl -H "x-apisports-key: YOUR_KEY" \
  "https://v3.football.api-sports.io/status" | \
  jq '.response.requests'
```

Returns:

```json
{
  "current": 15,
  "limit_day": 100
}
```

## Troubleshooting

### No lineups found

- Check if match has actually been played (not future test data)
- Verify fixture exists in API-Football
- Check team name mapping (may need normalization)

### Rate limit exceeded

- Wait for daily reset (midnight UTC)
- Reduce batch size in ingestion command
- Consider upgrading to paid tier if needed

### Player stats not showing

- Ensure ingestion has run for that match
- Check `player_match_stats` table for data
- Verify match is marked as FINISHED

## Cost Analysis

**Free Tier (Current):**

- 100 requests/day = ~30 matches/day
- Sufficient for MVP and demo
- Cost: $0/month

**Paid Tier (If needed):**

- 7,500 requests/day
- Covers ~2,500 matches/day
- Cost: $19/month
- Recommended for production with high traffic

## Next Steps

1. **Automate ingestion**: Set up daily cron job
2. **Backfill data**: Run ingestion for historical matches
3. **Monitor usage**: Track API quota consumption
4. **Enhance stats**: Add more metrics (shots, passes, tackles)
5. **Player profiles**: Use `GetPlayerStats()` for season-long stats

## Success Metrics

✅ API-Football client implemented and tested
✅ Lineup data successfully fetched
✅ Goals and assists extracted from events
✅ Player data stored in database
✅ Frontend displays key players
✅ 95 requests remaining today (5 used for testing)

## Example Output

When you run `make player-ingest`:

```
🔄 Starting player data ingestion...
   📊 Using API-Football for lineup data
   ⚠️  Rate limit: 100 requests/day (free tier)
   Fetching recent finished matches from database...
   Found 5 finished matches to process
   [1/5] Processing match 498761...
      ✅ Processed lineups (22 players, 5 goals, 3 assists)
      ⏳ Waiting 2 seconds...
   [2/5] Processing match 498065...
      ✅ Processed lineups (22 players, 3 goals, 2 assists)
      ⏳ Waiting 2 seconds...
   ...

✅ Player ingestion complete!
   Processed: 5 matches
   Skipped: 0 matches (already had data)
```

Then in your frontend, Ball Knowledge shows:

```
Key players
Home: O. Watkins (F) – 3 G, 1 A
      Douglas Luiz (M) – 1 G, 0 A

Away: Ansu Fati (F) – 1 G, 1 A
      João Pedro (F) – 0 G, 2 A
```
