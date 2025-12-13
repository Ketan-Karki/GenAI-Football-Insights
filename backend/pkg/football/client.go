package football

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	BaseURL = "https://api.football-data.org/v4"
)

type Client struct {
	apiKey     string
	httpClient *http.Client
}

func NewClient(apiKey string) *Client {
	return &Client{
		apiKey: apiKey,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *Client) doRequest(endpoint string) ([]byte, error) {
	url := fmt.Sprintf("%s%s", BaseURL, endpoint)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-Auth-Token", c.apiKey)
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	return body, nil
}

// GetCompetitions fetches available competitions
func (c *Client) GetCompetitions() (*CompetitionsResponse, error) {
	data, err := c.doRequest("/competitions")
	if err != nil {
		return nil, err
	}

	var response CompetitionsResponse
	if err := json.Unmarshal(data, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &response, nil
}

// GetMatches fetches matches for a competition
func (c *Client) GetMatches(competitionCode string, season string) (*MatchesResponse, error) {
	endpoint := fmt.Sprintf("/competitions/%s/matches", competitionCode)
	if season != "" {
		endpoint += fmt.Sprintf("?season=%s", season)
	}

	data, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var response MatchesResponse
	if err := json.Unmarshal(data, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &response, nil
}

// GetStandings fetches standings for a competition
func (c *Client) GetStandings(competitionCode string, season string) (*StandingsResponse, error) {
	endpoint := fmt.Sprintf("/competitions/%s/standings", competitionCode)
	if season != "" {
		endpoint += fmt.Sprintf("?season=%s", season)
	}

	data, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var response StandingsResponse
	if err := json.Unmarshal(data, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &response, nil
}

// GetMatch fetches a single match by ID
func (c *Client) GetMatch(matchID int) (*Match, error) {
	endpoint := fmt.Sprintf("/matches/%d", matchID)

	data, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var match Match
	if err := json.Unmarshal(data, &match); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &match, nil
}

// GetMatchLineups fetches lineups for a specific match by ID
// Note: Lineups are only available for finished matches or matches in progress
func (c *Client) GetMatchLineups(matchID int) (*MatchLineups, error) {
	endpoint := fmt.Sprintf("/matches/%d", matchID)

	data, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	// The match endpoint returns full match details including lineups
	// We need to extract just the lineup portion
	var fullMatch struct {
		HomeTeam struct {
			ID     int    `json:"id"`
			Name   string `json:"name"`
			Lineup []struct {
				ID          int    `json:"id"`
				Name        string `json:"name"`
				Position    string `json:"position"`
				ShirtNumber int    `json:"shirtNumber"`
			} `json:"lineup"`
			Formation string `json:"formation"`
			Coach     *Coach `json:"coach"`
		} `json:"homeTeam"`
		AwayTeam struct {
			ID     int    `json:"id"`
			Name   string `json:"name"`
			Lineup []struct {
				ID          int    `json:"id"`
				Name        string `json:"name"`
				Position    string `json:"position"`
				ShirtNumber int    `json:"shirtNumber"`
			} `json:"lineup"`
			Formation string `json:"formation"`
			Coach     *Coach `json:"coach"`
		} `json:"awayTeam"`
	}

	if err := json.Unmarshal(data, &fullMatch); err != nil {
		return nil, fmt.Errorf("failed to parse lineups: %w", err)
	}

	// Map to our MatchLineups structure
	lineups := &MatchLineups{}
	lineups.HomeTeam.ID = fullMatch.HomeTeam.ID
	lineups.HomeTeam.Name = fullMatch.HomeTeam.Name
	lineups.HomeTeam.Lineup.Formation = fullMatch.HomeTeam.Formation
	lineups.HomeTeam.Lineup.Coach = fullMatch.HomeTeam.Coach

	for _, p := range fullMatch.HomeTeam.Lineup {
		lineups.HomeTeam.Lineup.StartXI = append(lineups.HomeTeam.Lineup.StartXI, LineupPlayer{
			ID:          p.ID,
			Name:        p.Name,
			Position:    p.Position,
			ShirtNumber: p.ShirtNumber,
		})
	}

	lineups.AwayTeam.ID = fullMatch.AwayTeam.ID
	lineups.AwayTeam.Name = fullMatch.AwayTeam.Name
	lineups.AwayTeam.Lineup.Formation = fullMatch.AwayTeam.Formation
	lineups.AwayTeam.Lineup.Coach = fullMatch.AwayTeam.Coach

	for _, p := range fullMatch.AwayTeam.Lineup {
		lineups.AwayTeam.Lineup.StartXI = append(lineups.AwayTeam.Lineup.StartXI, LineupPlayer{
			ID:          p.ID,
			Name:        p.Name,
			Position:    p.Position,
			ShirtNumber: p.ShirtNumber,
		})
	}

	return lineups, nil
}

// GetTeamSquad fetches the full squad for a team by ID
func (c *Client) GetTeamSquad(teamID int) (*TeamSquad, error) {
	endpoint := fmt.Sprintf("/teams/%d", teamID)

	data, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var squad TeamSquad
	if err := json.Unmarshal(data, &squad); err != nil {
		return nil, fmt.Errorf("failed to parse squad: %w", err)
	}

	return &squad, nil
}
