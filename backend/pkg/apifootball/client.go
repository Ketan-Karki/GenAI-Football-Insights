package apifootball

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Client struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
}

func NewClient(apiKey string) *Client {
	return &Client{
		baseURL: "https://v3.football.api-sports.io",
		apiKey:  apiKey,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (c *Client) doRequest(endpoint string) ([]byte, error) {
	req, err := http.NewRequest("GET", c.baseURL+endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("x-apisports-key", c.apiKey)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	return body, nil
}

// GetFixtureLineups fetches lineups for a specific fixture
func (c *Client) GetFixtureLineups(fixtureID int) ([]FixtureLineupsResponse, error) {
	endpoint := fmt.Sprintf("/fixtures/lineups?fixture=%d", fixtureID)

	body, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var response struct {
		Response []FixtureLineupsResponse `json:"response"`
		Errors   []string                 `json:"errors"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	if len(response.Errors) > 0 {
		return nil, fmt.Errorf("API errors: %v", response.Errors)
	}

	return response.Response, nil
}

// GetFixtureEvents fetches events (goals, assists, etc.) for a fixture
func (c *Client) GetFixtureEvents(fixtureID int) ([]FixtureEvent, error) {
	endpoint := fmt.Sprintf("/fixtures/events?fixture=%d", fixtureID)

	body, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var response struct {
		Response []FixtureEvent `json:"response"`
		Errors   []string       `json:"errors"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	if len(response.Errors) > 0 {
		return nil, fmt.Errorf("API errors: %v", response.Errors)
	}

	return response.Response, nil
}

// GetPlayerStats fetches player statistics for a season
func (c *Client) GetPlayerStats(playerID, season int) ([]PlayerStatsResponse, error) {
	endpoint := fmt.Sprintf("/players?id=%d&season=%d", playerID, season)

	body, err := c.doRequest(endpoint)
	if err != nil {
		return nil, err
	}

	var response struct {
		Response []PlayerStatsResponse `json:"response"`
		Errors   []string              `json:"errors"`
	}

	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	if len(response.Errors) > 0 {
		return nil, fmt.Errorf("API errors: %v", response.Errors)
	}

	return response.Response, nil
}
