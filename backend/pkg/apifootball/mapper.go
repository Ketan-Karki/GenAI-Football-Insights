package apifootball

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// FixtureMapper helps map between football-data.org matches and API-Football fixtures
type FixtureMapper struct {
	client *Client
}

func NewFixtureMapper(client *Client) *FixtureMapper {
	return &FixtureMapper{client: client}
}

// FindFixtureByTeamsAndDate searches for an API-Football fixture matching the given criteria
// This is needed because football-data.org and API-Football use different IDs
func (m *FixtureMapper) FindFixtureByTeamsAndDate(homeTeamName, awayTeamName string, matchDate time.Time) (int, error) {
	// Format date as YYYY-MM-DD for API-Football
	dateStr := matchDate.Format("2006-01-02")

	endpoint := fmt.Sprintf("/fixtures?date=%s", dateStr)

	body, err := m.client.doRequest(endpoint)
	if err != nil {
		return 0, fmt.Errorf("failed to fetch fixtures: %w", err)
	}

	var response struct {
		Response []struct {
			Fixture struct {
				ID   int    `json:"id"`
				Date string `json:"date"`
			} `json:"fixture"`
			Teams struct {
				Home struct {
					ID   int    `json:"id"`
					Name string `json:"name"`
				} `json:"home"`
				Away struct {
					ID   int    `json:"id"`
					Name string `json:"name"`
				} `json:"away"`
			} `json:"teams"`
		} `json:"response"`
		Errors interface{} `json:"errors"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return 0, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	// Check for errors (can be array, object, or empty)
	if response.Errors != nil {
		if errMap, ok := response.Errors.(map[string]interface{}); ok && len(errMap) > 0 {
			return 0, fmt.Errorf("API errors: %v", response.Errors)
		}
		if errArr, ok := response.Errors.([]interface{}); ok && len(errArr) > 0 {
			return 0, fmt.Errorf("API errors: %v", response.Errors)
		}
	}

	// Find matching fixture by team names
	for _, fixture := range response.Response {
		if normalizeTeamName(fixture.Teams.Home.Name) == normalizeTeamName(homeTeamName) &&
			normalizeTeamName(fixture.Teams.Away.Name) == normalizeTeamName(awayTeamName) {
			return fixture.Fixture.ID, nil
		}
	}

	return 0, fmt.Errorf("no matching fixture found for %s vs %s on %s", homeTeamName, awayTeamName, dateStr)
}

// GetOrCreateFixtureMapping retrieves or creates a mapping between football-data.org match ID and API-Football fixture ID
func GetOrCreateFixtureMapping(db *sql.DB, mapper *FixtureMapper, matchID int, homeTeamName, awayTeamName string, matchDate time.Time) (int, error) {
	// Check if mapping already exists
	var fixtureID int
	err := db.QueryRow(`
		SELECT api_football_fixture_id 
		FROM match_fixture_mappings 
		WHERE football_data_match_id = $1
	`, matchID).Scan(&fixtureID)

	if err == nil {
		return fixtureID, nil
	}

	if err != sql.ErrNoRows {
		return 0, fmt.Errorf("failed to query mapping: %w", err)
	}

	// Mapping doesn't exist, find the fixture
	fixtureID, err = mapper.FindFixtureByTeamsAndDate(homeTeamName, awayTeamName, matchDate)
	if err != nil {
		return 0, err
	}

	// Store the mapping
	_, err = db.Exec(`
		INSERT INTO match_fixture_mappings (football_data_match_id, api_football_fixture_id, created_at)
		VALUES ($1, $2, NOW())
		ON CONFLICT (football_data_match_id) DO UPDATE SET api_football_fixture_id = EXCLUDED.api_football_fixture_id
	`, matchID, fixtureID)

	if err != nil {
		return 0, fmt.Errorf("failed to store mapping: %w", err)
	}

	return fixtureID, nil
}

// normalizeTeamName normalizes team names for comparison
func normalizeTeamName(name string) string {
	// Simple normalization - can be enhanced
	return strings.ToLower(strings.TrimSpace(name))
}
