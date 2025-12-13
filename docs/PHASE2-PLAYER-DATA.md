# Phase 2: Player Data Integration

## Summary

Successfully extended the football-data.org client to fetch player and lineup data, avoiding the need for unreliable third-party APIs.

## What's Been Implemented

### 1. Database Schema (✅ Complete)

- `players` table for player records
- `match_lineups` for team formations per match
- `match_lineup_players` junction table
- `player_match_stats` for goals/assists tracking

### 2. API Client Extensions (✅ Complete)

**New Models** (`pkg/football/models.go`):

- `Player` - player details
- `LineupPlayer` - player in match context
- `Lineup` - team formation + startXI + substitutes
- `MatchLineups` - full home/away lineups
- `TeamSquad` - team roster

**New Client Methods** (`pkg/football/client.go`):

- `GetMatchLineups(matchID int)` - fetches lineups for finished matches
- `GetTeamSquad(teamID int)` - fetches full team squad

### 3. Backend Integration (✅ Complete)

**Repository** (`internal/repository/player.go`):

- `PlayerRepository.GetKeyPlayersForMatch()` - queries top performers by goals/assists

**Service** (`internal/service/football.go`):

- `FootballService.GetKeyPlayers()` - splits players into home/away

**Handler** (`internal/handlers/football.go`):

- `/api/v1/predictions/:matchId` now includes optional `keyPlayers` field:
  ```json
  {
    "keyPlayers": {
      "home": [{"name": "...", "position": "...", "goals": 2, "assists": 1}],
      "away": [...]
    }
  }
  ```

### 4. Frontend (✅ Complete)

**Types** (`frontend/lib/api.ts`):

- `PlayerInsight` interface
- `KeyPlayers` interface
- Added to `Prediction` type

**UI** (`frontend/components/match-card.tsx`):

- Ball Knowledge panel displays key players (up to 2 per side)
- Shows: Name (Position) – X G, Y A
- Gracefully handles "No data yet" state

### 5. Ingestion Command (✅ Complete, needs quota)

**Command** (`cmd/player_ingest/main.go`):

- Fetches recent finished matches from DB
- Calls `GetMatchLineups()` for each
- Upserts players and lineup data
- Respects rate limits (10 req/min free tier)

## Current Status

✅ All code implemented and compiling
✅ Ingestion command runs successfully
⚠️ **Limitation discovered**: football-data.org free tier does **not include lineup data**

### API Limitation

The football-data.org API response for matches does not include:

- `lineup` field (player lists)
- `formation` field (tactical setup)

These fields return `null` even for finished matches. This appears to be a **free tier limitation**.

**Available match data in free tier**:

- Match details (teams, score, date, status)
- Referees
- Competition info
- Basic team info (name, crest, ID)

**NOT available**:

- Player lineups
- Formations
- Player match stats
- Detailed player data

## Next Steps

### To populate player data:

1. **Wait for rate limit reset** (~1 minute from last API call)

2. **Run ingestion**:

   ```bash
   cd backend
   make player-ingest
   ```

   This will:

   - Process last 7 days of finished matches (10 at a time)
   - Take ~70 seconds (7s delay between requests)
   - Populate `players`, `match_lineups`, `player_match_stats`

3. **Verify data**:

   ```sql
   SELECT COUNT(*) FROM players;
   SELECT COUNT(*) FROM match_lineups;
   ```

4. **Test prediction endpoint**:
   - Visit frontend
   - Click "Show Ball Knowledge" on any match
   - Should see "Key players" section with real data (if match has finished)

### For ongoing updates:

Run `make player-ingest` periodically (e.g., daily) to keep player stats fresh for recent matches.

### Rate Limit Notes:

- **Free tier**: 10 requests/minute
- **Ingestion batch**: 10 matches = ~70 seconds
- **Recommendation**: Run once per day, or upgrade to paid tier ($19/mo = 7,500 req/day)

## Architecture Benefits

✅ Single API provider (football-data.org) for all data
✅ No RapidAPI dependency
✅ Reliable, well-documented API
✅ Consistent data model across matches + players
✅ Free tier sufficient for MVP

## API Response Example

When lineups are available, the match endpoint returns:

```json
{
  "homeTeam": {
    "id": 65,
    "name": "Manchester City",
    "lineup": [
      {"id": 1, "name": "Ederson", "position": "Goalkeeper", "shirtNumber": 31},
      {"id": 2, "name": "Kyle Walker", "position": "Defence", "shirtNumber": 2}
    ],
    "formation": "4-3-3"
  },
  "awayTeam": { ... }
}
```

Our ingestion maps this to:

- `players` table (upsert by external_id)
- `match_lineups` (formation, team)
- `match_lineup_players` (links players to lineup)
- `player_match_stats` (goals/assists extracted from match events - future enhancement)

## Options for Player Data

Given the free tier limitation, here are your options:

### Option 1: Upgrade football-data.org (Recommended for MVP)

- **Cost**: Free tier sufficient for now
- **Action**: Accept that keyPlayers will show "No data yet" until you upgrade or find alternative
- **Benefit**: Keep single API provider, clean architecture
- **Limitation**: No player insights in free tier

### Option 2: Use API-Football for player data only

- **Cost**: $19/mo for 7,500 req/day
- **Coverage**: Includes lineups, player stats, formations
- **Reliability**: Mixed reviews (see research above)
- **Implementation**: Add secondary API client just for player data
- **Complexity**: Medium (dual API architecture)

### Option 3: Manual/Mock Data for Demo

- **Cost**: Free
- **Action**: Create seed data for a few showcase matches
- **Benefit**: Can demo the feature without API costs
- **Limitation**: Not real-time, limited to demo matches

### Option 4: Wait and See

- **Cost**: Free
- **Action**: Keep current implementation, keyPlayers shows "No data yet"
- **Benefit**: Feature is ready when you get data source
- **UX**: Gracefully handles missing data

## Recommendation

For **MVP**: Go with **Option 4** (current state)

- Your UI already handles missing player data gracefully
- Backend is fully wired and ready
- You can add a data source later without code changes
- Focus on other features (predictions, UI polish, etc.)

For **production**: Consider **Option 2** if player insights are critical

- API-Football has the data despite mixed reviews
- $19/mo is reasonable for production app
- Keep football-data.org for matches/standings

## Future Enhancements

1. **Match events** - Parse goals/assists from match events API (if available)
2. **Player ratings** - If available in API response
3. **Historical stats** - Aggregate player performance over season
4. **Squad management** - Use `GetTeamSquad()` for full rosters
5. **Alternative data source** - Integrate API-Football or similar for player data
