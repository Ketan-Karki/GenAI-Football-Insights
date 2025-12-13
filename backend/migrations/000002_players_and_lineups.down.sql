-- Rollback Phase 2: players, lineups, and player match stats

DROP INDEX IF EXISTS idx_player_stats_player;
DROP INDEX IF EXISTS idx_player_stats_match;
DROP INDEX IF EXISTS idx_lineup_players_lineup;
DROP INDEX IF EXISTS idx_lineups_match_team;
DROP INDEX IF EXISTS idx_player_team;

DROP TABLE IF EXISTS player_match_stats;
DROP TABLE IF EXISTS match_lineup_players;
DROP TABLE IF EXISTS match_lineups;
DROP TABLE IF EXISTS players;
