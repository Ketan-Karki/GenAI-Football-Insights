-- Migration: Enhanced features for team-agnostic prediction model
-- This adds xG, player stats, tactical data, and prediction history

-- Player statistics per match (enhanced with xG)
CREATE TABLE IF NOT EXISTS player_match_stats_enhanced (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    match_id INT REFERENCES matches(id),
    minutes_played INT DEFAULT 0,
    xg DECIMAL(4,2) DEFAULT 0.0,
    shots INT DEFAULT 0,
    shots_on_target INT DEFAULT 0,
    key_passes INT DEFAULT 0,
    successful_dribbles INT DEFAULT 0,
    tackles_won INT DEFAULT 0,
    interceptions INT DEFAULT 0,
    pass_completion_rate DECIMAL(4,2) DEFAULT 0.0,
    position VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, match_id)
);

-- Team tactical data per season
CREATE TABLE IF NOT EXISTS team_tactics (
    id SERIAL PRIMARY KEY,
    team_id INT REFERENCES teams(id),
    season VARCHAR(10) NOT NULL,
    formation VARCHAR(10),
    avg_possession DECIMAL(4,2) DEFAULT 0.0,
    pressing_intensity DECIMAL(4,2) DEFAULT 0.0,
    avg_passes_per_game INT DEFAULT 0,
    avg_shots_per_game INT DEFAULT 0,
    xg_per_game DECIMAL(4,2) DEFAULT 0.0,
    xg_conceded_per_game DECIMAL(4,2) DEFAULT 0.0,
    defensive_rating DECIMAL(4,2) DEFAULT 0.0,
    attacking_rating DECIMAL(4,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, season)
);

-- Match context data (xG, possession, shots, etc.)
CREATE TABLE IF NOT EXISTS match_context (
    match_id INT PRIMARY KEY REFERENCES matches(id),
    team_a_formation VARCHAR(10),
    team_b_formation VARCHAR(10),
    team_a_xg DECIMAL(4,2) DEFAULT 0.0,
    team_b_xg DECIMAL(4,2) DEFAULT 0.0,
    team_a_possession DECIMAL(4,2) DEFAULT 0.0,
    team_b_possession DECIMAL(4,2) DEFAULT 0.0,
    team_a_shots INT DEFAULT 0,
    team_b_shots INT DEFAULT 0,
    team_a_shots_on_target INT DEFAULT 0,
    team_b_shots_on_target INT DEFAULT 0,
    team_a_corners INT DEFAULT 0,
    team_b_corners INT DEFAULT 0,
    team_a_fouls INT DEFAULT 0,
    team_b_fouls INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prediction history for tracking and learning
CREATE TABLE IF NOT EXISTS prediction_history (
    id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(id),
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Team names (for display)
    team_a_name VARCHAR(100),
    team_b_name VARCHAR(100),
    
    -- Predicted values
    predicted_team_a_goals DECIMAL(3,1),
    predicted_team_b_goals DECIMAL(3,1),
    predicted_outcome VARCHAR(100),
    predicted_winner VARCHAR(100),
    confidence_score DECIMAL(4,2),
    
    -- Actual values (filled after match finishes)
    actual_team_a_goals INT,
    actual_team_b_goals INT,
    actual_outcome VARCHAR(100),
    actual_winner VARCHAR(100),
    prediction_correct BOOLEAN,
    
    -- For analysis and learning
    features_used JSONB,
    insights_generated TEXT[],
    model_version VARCHAR(50),
    
    -- Error metrics
    goals_error_team_a DECIMAL(3,1),
    goals_error_team_b DECIMAL(3,1),
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id)
);

-- Coach data
CREATE TABLE IF NOT EXISTS coaches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Team coach assignments
CREATE TABLE IF NOT EXISTS team_coaches (
    id SERIAL PRIMARY KEY,
    team_id INT REFERENCES teams(id),
    coach_id INT REFERENCES coaches(id),
    season VARCHAR(10) NOT NULL,
    start_date DATE,
    end_date DATE,
    matches_managed INT DEFAULT 0,
    wins INT DEFAULT 0,
    draws INT DEFAULT 0,
    losses INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, coach_id, season)
);

-- Injuries and suspensions
CREATE TABLE IF NOT EXISTS player_availability (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    team_id INT REFERENCES teams(id),
    unavailable_from DATE NOT NULL,
    unavailable_until DATE,
    reason VARCHAR(50), -- 'injury', 'suspension', 'other'
    severity VARCHAR(20), -- 'minor', 'moderate', 'severe'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_match_stats_enhanced_player ON player_match_stats_enhanced(player_id);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_enhanced_match ON player_match_stats_enhanced(match_id);
CREATE INDEX IF NOT EXISTS idx_team_tactics_team_season ON team_tactics(team_id, season);
CREATE INDEX IF NOT EXISTS idx_prediction_history_match ON prediction_history(match_id);
CREATE INDEX IF NOT EXISTS idx_prediction_history_predicted_at ON prediction_history(predicted_at DESC);
CREATE INDEX IF NOT EXISTS idx_team_coaches_team_season ON team_coaches(team_id, season);
CREATE INDEX IF NOT EXISTS idx_player_availability_player ON player_availability(player_id);
CREATE INDEX IF NOT EXISTS idx_player_availability_dates ON player_availability(unavailable_from, unavailable_until);

-- Comments for documentation
COMMENT ON TABLE player_match_stats_enhanced IS 'Enhanced player statistics including xG and detailed performance metrics';
COMMENT ON TABLE team_tactics IS 'Team tactical data and playing style per season';
COMMENT ON TABLE match_context IS 'Detailed match context including xG, possession, and shots';
COMMENT ON TABLE prediction_history IS 'Historical predictions for model learning and user display';
COMMENT ON COLUMN prediction_history.features_used IS 'JSON object containing all features used for this prediction';
COMMENT ON COLUMN prediction_history.insights_generated IS 'Array of insights shown to user';
