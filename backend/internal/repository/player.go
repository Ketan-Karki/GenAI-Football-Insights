package repository

import (
	"database/sql"
	"fmt"
)

// PlayerInsight represents a simple summary of a player's impact in a match.
type PlayerInsight struct {
	Name           string   `json:"name"`
	Position       string   `json:"position"`
	TeamExternalID int      `json:"teamExternalId"`
	Goals          int      `json:"goals"`
	Assists        int      `json:"assists"`
	Rating         *float64 `json:"rating,omitempty"`
}

// PlayerRepository provides DB access for player-related data.
type PlayerRepository struct {
	db *sql.DB
}

func NewPlayerRepository(db *sql.DB) *PlayerRepository {
	return &PlayerRepository{db: db}
}

// GetKeyPlayersForMatch returns top players for a given match external ID.
// This uses the player_match_stats data if available. If there is no data,
// it returns an empty slice and no error.
func (r *PlayerRepository) GetKeyPlayersForMatch(matchExternalID int, limit int) ([]PlayerInsight, error) {
	const query = `
        SELECT
            p.name,
            COALESCE(p.position, ''),
            t.external_id,
            COALESCE(s.goals, 0) AS goals,
            COALESCE(s.assists, 0) AS assists,
            s.rating
        FROM player_match_stats s
        JOIN matches m ON m.id = s.match_id
        JOIN players p ON p.id = s.player_id
        JOIN teams t ON p.team_id = t.id
        WHERE m.external_id = $1
        ORDER BY goals DESC, assists DESC, COALESCE(rating, 0) DESC
        LIMIT $2
    `

	rows, err := r.db.Query(query, matchExternalID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query key players: %w", err)
	}
	defer rows.Close()

	var result []PlayerInsight

	for rows.Next() {
		var (
			name     string
			position string
			teamExt  int
			goals    int
			assists  int
			rating   sql.NullFloat64
		)

		if err := rows.Scan(&name, &position, &teamExt, &goals, &assists, &rating); err != nil {
			return nil, fmt.Errorf("failed to scan key player: %w", err)
		}

		var ratingPtr *float64
		if rating.Valid {
			v := rating.Float64
			ratingPtr = &v
		}

		pi := PlayerInsight{
			Name:           name,
			Position:       position,
			TeamExternalID: teamExt,
			Goals:          goals,
			Assists:        assists,
			Rating:         ratingPtr,
		}

		// Caller will decide which team this belongs to based on TeamExternalID.
		result = append(result, pi)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("key players rows error: %w", err)
	}

	// Note: we don't split into home/away here; service layer will do that once
	// it knows the current match's home and away team external IDs.
	return result, nil
}
