package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/yourusername/football-prediction/internal/service"
	"github.com/yourusername/football-prediction/pkg/football"
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

	// Get match details to send to ML service
	match, err := h.service.GetMatch(matchID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get match details"})
		return
	}

	// Best-effort head-to-head statistics (do not fail on error)
	var headToHead gin.H
	if h2h, err := h.service.GetHeadToHead(match.HomeTeam.ID, match.AwayTeam.ID, 10); err == nil && h2h != nil {
		headToHead = gin.H{
			"homeWins": h2h.HomeWins,
			"awayWins": h2h.AwayWins,
			"draws":    h2h.Draws,
		}
	}

	// Best-effort key players based on stored player_match_stats (do not fail on error)
	var keyPlayers gin.H
	if homeKP, awayKP, err := h.service.GetKeyPlayers(match.ID, match.HomeTeam.ID, match.AwayTeam.ID, 6); err == nil {
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

	// Prepare request payload
	payload := map[string]interface{}{
		"home_team_id": match.HomeTeam.ID,
		"away_team_id": match.AwayTeam.ID,
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

	// Add ball knowledge insights using raw ML response (includes team_stats)
	prediction["ballKnowledge"] = generateBallKnowledge(match, mlResponse)

	c.JSON(http.StatusOK, prediction)
}

func generateBallKnowledge(match *football.Match, ml map[string]interface{}) []string {
	insights := []string{}

	homeWinProb, _ := ml["home_win_probability"].(float64)
	awayWinProb, _ := ml["away_win_probability"].(float64)
	drawProb, _ := ml["draw_probability"].(float64)
	confidence, _ := ml["confidence_score"].(float64)

	// Optional team_stats block
	var homeForm, awayForm, homeGoals, awayGoals float64
	if tsRaw, ok := ml["team_stats"].(map[string]interface{}); ok {
		if v, ok := tsRaw["home_form"].(float64); ok {
			homeForm = v
		}
		if v, ok := tsRaw["away_form"].(float64); ok {
			awayForm = v
		}
		if v, ok := tsRaw["home_goals_avg"].(float64); ok {
			homeGoals = v
		}
		if v, ok := tsRaw["away_goals_avg"].(float64); ok {
			awayGoals = v
		}
	}

	// Main prediction with context
	predictedOutcome, _ := ml["predicted_outcome"].(string)
	if predictedOutcome == "HOME_WIN" {
		insights = append(insights, fmt.Sprintf("🏆 AI predicts %s victory at home", match.HomeTeam.ShortName))
		insights = append(insights, fmt.Sprintf("📊 Win probability: %.0f%%", homeWinProb*100))
	} else if predictedOutcome == "AWAY_WIN" {
		insights = append(insights, fmt.Sprintf("🏆 AI predicts %s to win away", match.AwayTeam.ShortName))
		insights = append(insights, fmt.Sprintf("📊 Win probability: %.0f%%", awayWinProb*100))
	} else if predictedOutcome == "DRAW" {
		insights = append(insights, "🤝 AI expects a draw - both teams rated closely")
		insights = append(insights, fmt.Sprintf("📊 Draw probability: %.0f%%", drawProb*100))
	}

	// Form-based insight (only if we have stats)
	if homeForm > 0 && awayForm > 0 {
		insights = append(insights,
			fmt.Sprintf("📈 Recent form: %s %.0f%% wins vs %s %.0f%%", match.HomeTeam.ShortName, homeForm*100, match.AwayTeam.ShortName, awayForm*100))
	}

	// Goals-based insight
	if homeGoals > 0 && awayGoals > 0 {
		insights = append(insights,
			fmt.Sprintf("⚽ Goals per game: %s %.1f vs %s %.1f", match.HomeTeam.ShortName, homeGoals, match.AwayTeam.ShortName, awayGoals))
	}

	// Confidence interpretation
	if confidence >= 0.7 {
		insights = append(insights, "✅ High confidence prediction from historical data")
	} else if confidence >= 0.55 {
		insights = append(insights, "� Medium confidence - data leans towards this result")
	} else {
		insights = append(insights, "⚠️ Low confidence - model sees this as a close matchup")
	}

	return insights
}
