package repository

import (
	"database/sql"
	"fmt"
)

// HeadToHeadMatch represents a single historical meeting between two teams.
type HeadToHeadMatch struct {
	Season             string `json:"season"`
	HomeTeamExternalID int    `json:"homeTeamExternalId"`
	AwayTeamExternalID int    `json:"awayTeamExternalId"`
	HomeScore          int    `json:"homeScore"`
	AwayScore          int    `json:"awayScore"`
	Winner             string `json:"winner"`
}

// HeadToHeadRecord aggregates the record between two clubs.
type HeadToHeadRecord struct {
	HomeWins int               `json:"homeWins"`
	AwayWins int               `json:"awayWins"`
	Draws    int               `json:"draws"`
	Matches  []HeadToHeadMatch `json:"lastMeetings"`
}

// MatchRepository provides DB access for matches and related stats.
type MatchRepository struct {
	db *sql.DB
}

func NewMatchRepository(db *sql.DB) *MatchRepository {
	return &MatchRepository{db: db}
}

// GetMatchByExternalID fetches a match from the database by its external API ID
func (r *MatchRepository) GetMatchByExternalID(externalID int) (map[string]interface{}, error) {
	query := `
		SELECT 
			m.id, m.external_id, m.status, m.utc_date, m.matchday,
			m.home_team_id, m.away_team_id,
			ht.name as home_team_name, ht.external_id as home_team_external_id,
			at.name as away_team_name, at.external_id as away_team_external_id
		FROM matches m
		JOIN teams ht ON m.home_team_id = ht.id
		JOIN teams at ON m.away_team_id = at.id
		WHERE m.external_id = $1
	`

	var (
		id, externalIDResult, homeTeamID, awayTeamID, homeExtID, awayExtID, matchday int
		status, homeTeamName, awayTeamName                                           string
		utcDate                                                                      sql.NullTime
	)

	err := r.db.QueryRow(query, externalID).Scan(
		&id, &externalIDResult, &status, &utcDate, &matchday,
		&homeTeamID, &awayTeamID,
		&homeTeamName, &homeExtID,
		&awayTeamName, &awayExtID,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("match not found")
		}
		return nil, fmt.Errorf("failed to fetch match: %w", err)
	}

	return map[string]interface{}{
		"id":         id,
		"externalId": externalIDResult,
		"status":     status,
		"utcDate":    utcDate.Time,
		"matchday":   matchday,
		"homeTeam": map[string]interface{}{
			"id":         homeTeamID,
			"externalId": homeExtID,
			"name":       homeTeamName,
		},
		"awayTeam": map[string]interface{}{
			"id":         awayTeamID,
			"externalId": awayExtID,
			"name":       awayTeamName,
		},
	}, nil
}

// GetMatchByID fetches a match from the database by its internal ID
func (r *MatchRepository) GetMatchByID(matchID int) (map[string]interface{}, error) {
	query := `
		SELECT 
			m.id, m.external_id, m.status, m.utc_date, m.matchday,
			m.home_team_id, m.away_team_id,
			ht.name as home_team_name, ht.external_id as home_team_external_id,
			at.name as away_team_name, at.external_id as away_team_external_id
		FROM matches m
		JOIN teams ht ON m.home_team_id = ht.id
		JOIN teams at ON m.away_team_id = at.id
		WHERE m.id = $1
	`

	var (
		id, externalID, homeTeamID, awayTeamID, homeExtID, awayExtID, matchday int
		status, homeTeamName, awayTeamName                                     string
		utcDate                                                                sql.NullTime
	)

	err := r.db.QueryRow(query, matchID).Scan(
		&id, &externalID, &status, &utcDate, &matchday,
		&homeTeamID, &awayTeamID,
		&homeTeamName, &homeExtID,
		&awayTeamName, &awayExtID,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("match not found")
		}
		return nil, fmt.Errorf("failed to fetch match: %w", err)
	}

	return map[string]interface{}{
		"id":         id,
		"externalId": externalID,
		"status":     status,
		"utcDate":    utcDate.Time,
		"matchday":   matchday,
		"homeTeam": map[string]interface{}{
			"id":         homeTeamID,
			"externalId": homeExtID,
			"name":       homeTeamName,
		},
		"awayTeam": map[string]interface{}{
			"id":         awayTeamID,
			"externalId": awayExtID,
			"name":       awayTeamName,
		},
	}, nil
}

// GetHeadToHeadByExternalTeamIDs returns head-to-head record for two clubs
// identified by their external IDs (from football-data.org).
func (r *MatchRepository) GetHeadToHeadByExternalTeamIDs(homeExternalID, awayExternalID, limit int) (*HeadToHeadRecord, error) {
	const query = `
        SELECT
            m.season,
            m.home_score,
            m.away_score,
            m.winner,
            th.external_id AS home_external_id,
            ta.external_id AS away_external_id
        FROM matches m
        JOIN teams th ON m.home_team_id = th.id
        JOIN teams ta ON m.away_team_id = ta.id
        WHERE ((th.external_id = $1 AND ta.external_id = $2)
            OR (th.external_id = $2 AND ta.external_id = $1))
          AND m.home_score IS NOT NULL
          AND m.away_score IS NOT NULL
        ORDER BY m.utc_date DESC
        LIMIT $3
    `

	rows, err := r.db.Query(query, homeExternalID, awayExternalID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query head-to-head: %w", err)
	}
	defer rows.Close()

	record := &HeadToHeadRecord{}

	for rows.Next() {
		var (
			season                       string
			homeScore, awayScore         int
			winner                       string
			rowHomeExternalID, rowAwayID int
		)

		if err := rows.Scan(&season, &homeScore, &awayScore, &winner, &rowHomeExternalID, &rowAwayID); err != nil {
			return nil, fmt.Errorf("failed to scan head-to-head row: %w", err)
		}

		// Count results from the perspective of the current home/away clubs,
		// regardless of who was home in the historical fixture.
		switch winner {
		case "DRAW":
			record.Draws++
		case "HOME_TEAM":
			if rowHomeExternalID == homeExternalID {
				record.HomeWins++
			} else if rowHomeExternalID == awayExternalID {
				record.AwayWins++
			}
		case "AWAY_TEAM":
			if rowAwayID == homeExternalID {
				record.HomeWins++
			} else if rowAwayID == awayExternalID {
				record.AwayWins++
			}
		}

		record.Matches = append(record.Matches, HeadToHeadMatch{
			Season:             season,
			HomeTeamExternalID: rowHomeExternalID,
			AwayTeamExternalID: rowAwayID,
			HomeScore:          homeScore,
			AwayScore:          awayScore,
			Winner:             winner,
		})
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("head-to-head rows error: %w", err)
	}

	// If no matches found, return nil so callers can decide what to do.
	if len(record.Matches) == 0 {
		return nil, nil
	}

	return record, nil
}
