-- Drop triggers
DROP TRIGGER IF EXISTS update_standings_updated_at ON standings;
DROP TRIGGER IF EXISTS update_matches_updated_at ON matches;
DROP TRIGGER IF EXISTS update_teams_updated_at ON teams;
DROP TRIGGER IF EXISTS update_competitions_updated_at ON competitions;

-- Drop trigger function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_predictions_match;
DROP INDEX IF EXISTS idx_standings_position;
DROP INDEX IF EXISTS idx_standings_competition_season;
DROP INDEX IF EXISTS idx_matches_teams;
DROP INDEX IF EXISTS idx_matches_status;
DROP INDEX IF EXISTS idx_matches_date;
DROP INDEX IF EXISTS idx_matches_competition;

-- Drop tables
DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS standings;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS competitions;
