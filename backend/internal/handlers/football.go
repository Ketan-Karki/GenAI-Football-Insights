package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/yourusername/football-prediction/internal/service"
)

type FootballHandler struct {
	service *service.FootballService
}

func NewFootballHandler(service *service.FootballService) *FootballHandler {
	return &FootballHandler{service: service}
}

func (h *FootballHandler) GetCompetitions(c *gin.Context) {
	competitions, err := h.service.GetCompetitions()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"count":        len(competitions),
		"competitions": competitions,
	})
}

func (h *FootballHandler) GetMatches(c *gin.Context) {
	competition := c.Query("competition")
	season := c.Query("season")

	if competition == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "competition parameter is required"})
		return
	}

	matches, err := h.service.GetMatches(competition, season)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, matches)
}

func (h *FootballHandler) GetMatch(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid match ID"})
		return
	}

	match, err := h.service.GetMatch(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, match)
}

func (h *FootballHandler) GetStandings(c *gin.Context) {
	competition := c.Param("competition")
	season := c.Query("season")

	standings, err := h.service.GetStandings(competition, season)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, standings)
}

func (h *FootballHandler) GetPrediction(c *gin.Context) {
	matchIDStr := c.Param("matchId")
	matchID, err := strconv.Atoi(matchIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid match ID"})
		return
	}

	// Get match details from database - try external ID first (from API), then internal ID
	matchData, err := h.service.GetMatchByExternalID(matchID)
	if err != nil {
		// If not found by external ID, try internal ID
		matchData, err = h.service.GetMatchFromDB(matchID)
		if err != nil {
			// If still not found, fetch from API as fallback
			match, apiErr := h.service.GetMatch(matchID)
			if apiErr != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get match details"})
				return
			}
			// Convert Match struct to map for processing
			matchData = map[string]interface{}{
				"id":       match.ID,
				"matchday": match.Matchday,
				"homeTeam": map[string]interface{}{
					"id":         match.HomeTeam.ID,
					"externalId": match.HomeTeam.ID,
					"name":       match.HomeTeam.Name,
				},
				"awayTeam": map[string]interface{}{
					"id":         match.AwayTeam.ID,
					"externalId": match.AwayTeam.ID,
					"name":       match.AwayTeam.Name,
				},
			}
		}
	}

	homeTeam := matchData["homeTeam"].(map[string]interface{})
	awayTeam := matchData["awayTeam"].(map[string]interface{})
	homeTeamID := homeTeam["id"].(int)
	awayTeamID := awayTeam["id"].(int)
	homeTeamExtID := homeTeam["externalId"].(int)
	awayTeamExtID := awayTeam["externalId"].(int)

	// Best-effort head-to-head statistics (do not fail on error)
	var headToHead gin.H
	if h2h, err := h.service.GetHeadToHead(homeTeamID, awayTeamID, 10); err == nil && h2h != nil {
		headToHead = gin.H{
			"homeWins": h2h.HomeWins,
			"awayWins": h2h.AwayWins,
			"draws":    h2h.Draws,
		}
	}

	// Best-effort key players based on stored player_match_stats (do not fail on error)
	var keyPlayers gin.H
	if homeKP, awayKP, err := h.service.GetKeyPlayers(matchID, homeTeamID, awayTeamID, 6); err == nil {
		// Only include if we have at least one player on either side
		if len(homeKP) > 0 || len(awayKP) > 0 {
			keyPlayers = gin.H{
				"home": homeKP,
				"away": awayKP,
			}
		}
	}

	// Call ML service for prediction
	mlServiceURL := os.Getenv("ML_SERVICE_URL")
	if mlServiceURL == "" {
		mlServiceURL = "http://localhost:8000"
	}

	// Prepare request payload using external IDs for ML service
	matchday := 1 // default
	if md, ok := matchData["matchday"].(int); ok {
		matchday = md
	}

	homeTeamName := homeTeam["name"].(string)
	awayTeamName := awayTeam["name"].(string)

	payload := map[string]interface{}{
		"home_team_id":   homeTeamExtID,
		"away_team_id":   awayTeamExtID,
		"matchday":       matchday,
		"home_team_name": homeTeamName,
		"away_team_name": awayTeamName,
	}

	jsonData, _ := json.Marshal(payload)
	resp, err := http.Post(mlServiceURL+"/predict", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		// Fallback to mock if ML service unavailable
		c.JSON(http.StatusOK, gin.H{
			"matchId":            matchID,
			"homeWinProbability": 0.45,
			"drawProbability":    0.30,
			"awayWinProbability": 0.25,
			"predictedOutcome":   "HOME_WIN",
			"confidenceScore":    0.65,
			"modelVersion":       "fallback",
		})
		return
	}
	defer resp.Body.Close()

	var mlResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&mlResponse); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to parse prediction"})
		return
	}

	// Convert snake_case to camelCase for frontend
	prediction := gin.H{
		"matchId":            matchID,
		"homeWinProbability": mlResponse["home_win_probability"],
		"drawProbability":    mlResponse["draw_probability"],
		"awayWinProbability": mlResponse["away_win_probability"],
		"predictedOutcome":   mlResponse["predicted_outcome"],
		"confidenceScore":    mlResponse["confidence_score"],
		"modelVersion":       mlResponse["model_version"],
	}

	// Map team_stats (if present) to camelCase teamStats
	if tsRaw, ok := mlResponse["team_stats"].(map[string]interface{}); ok {
		prediction["teamStats"] = gin.H{
			"homeForm":     tsRaw["home_form"],
			"awayForm":     tsRaw["away_form"],
			"homeGoalsAvg": tsRaw["home_goals_avg"],
			"awayGoalsAvg": tsRaw["away_goals_avg"],
			"homeWinRate":  tsRaw["home_win_rate"],
			"awayWinRate":  tsRaw["away_win_rate"],
		}
	}

	// Attach head-to-head summary if available
	if headToHead != nil {
		prediction["headToHead"] = headToHead
	}

	// Attach keyPlayers if available
	if keyPlayers != nil {
		prediction["keyPlayers"] = keyPlayers
	}

	// Add team-specific prediction winner
	predictedOutcome, _ := prediction["predictedOutcome"].(string)
	// homeTeamName and awayTeamName already declared above

	var predictedWinner string
	switch predictedOutcome {
	case "HOME_WIN":
		predictedWinner = homeTeamName
	case "AWAY_WIN":
		predictedWinner = awayTeamName
	case "DRAW":
		predictedWinner = "Draw"
	default:
		predictedWinner = predictedOutcome
	}
	prediction["predictedWinner"] = predictedWinner
	prediction["homeTeam"] = homeTeamName
	prediction["awayTeam"] = awayTeamName

	// Add insights from ML response if available
	if insights, ok := mlResponse["insights"].([]interface{}); ok {
		prediction["insights"] = insights
	}

	// Add model accuracy if available
	if accuracy, ok := mlResponse["model_accuracy"].(float64); ok {
		prediction["modelAccuracy"] = accuracy
	}

	c.JSON(http.StatusOK, prediction)
}
