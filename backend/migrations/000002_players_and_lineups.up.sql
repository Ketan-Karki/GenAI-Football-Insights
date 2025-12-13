-- Phase 2: players, lineups, and player match stats

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE NOT NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(50),
    shirt_number INTEGER,
    nationality VARCHAR(100),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match lineups (per team per match)
CREATE TABLE IF NOT EXISTS match_lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    is_home BOOLEAN NOT NULL,
    formation VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, team_id)
);

-- Players appearing in a lineup
CREATE TABLE IF NOT EXISTS match_lineup_players (
    id SERIAL PRIMARY KEY,
    match_lineup_id INTEGER REFERENCES match_lineups(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    role VARCHAR(20),          -- starter / substitute
    position VARCHAR(20),      -- e.g. GK, RB, CM
    minutes_played INTEGER,
    UNIQUE(match_lineup_id, player_id)
);

-- Per-player match statistics (aggregated from provider)
CREATE TABLE IF NOT EXISTS player_match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    key_passes INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    rating NUMERIC(4,2),
    minutes_played INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_player_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_lineups_match_team ON match_lineups(match_id, team_id);
CREATE INDEX IF NOT EXISTS idx_lineup_players_lineup ON match_lineup_players(match_lineup_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_match ON player_match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_match_stats(player_id);
