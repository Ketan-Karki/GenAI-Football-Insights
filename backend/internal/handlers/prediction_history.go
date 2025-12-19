package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/lib/pq"
)

type PredictionHistory struct {
	ID                  int      `json:"id"`
	MatchID             int      `json:"matchId"`
	PredictedAt         string   `json:"predictedAt"`
	TeamAName           string   `json:"teamAName"`
	TeamBName           string   `json:"teamBName"`
	PredictedTeamAGoals float64  `json:"predictedTeamAGoals"`
	PredictedTeamBGoals float64  `json:"predictedTeamBGoals"`
	PredictedOutcome    string   `json:"predictedOutcome"`
	PredictedWinner     string   `json:"predictedWinner"`
	ConfidenceScore     float64  `json:"confidenceScore"`
	ActualTeamAGoals    *int     `json:"actualTeamAGoals"`
	ActualTeamBGoals    *int     `json:"actualTeamBGoals"`
	ActualOutcome       *string  `json:"actualOutcome"`
	ActualWinner        *string  `json:"actualWinner"`
	PredictionCorrect   *bool    `json:"predictionCorrect"`
	Insights            []string `json:"insights"`
	ModelVersion        string   `json:"modelVersion"`
	GoalsErrorTeamA     *float64 `json:"goalsErrorTeamA"`
	GoalsErrorTeamB     *float64 `json:"goalsErrorTeamB"`
	MatchDate           string   `json:"matchDate"`
}

// GetPredictionHistory returns prediction history with actual results
func GetPredictionHistory(c *gin.Context, db *sql.DB) {
	limitStr := c.DefaultQuery("limit", "50")
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit > 100 {
		limit = 50
	}

	query := `
		SELECT 
			ph.id,
			ph.match_id,
			ph.predicted_at,
			ph.team_a_name,
			ph.team_b_name,
			ph.predicted_team_a_goals,
			ph.predicted_team_b_goals,
			ph.predicted_outcome,
			ph.predicted_winner,
			ph.confidence_score,
			ph.actual_team_a_goals,
			ph.actual_team_b_goals,
			ph.actual_outcome,
			ph.actual_winner,
			ph.prediction_correct,
			ph.insights_generated,
			ph.model_version,
			ph.goals_error_team_a,
			ph.goals_error_team_b,
			m.utc_date
		FROM prediction_history ph
		JOIN matches m ON ph.match_id = m.id
		WHERE ph.actual_team_a_goals IS NOT NULL
		ORDER BY m.utc_date DESC
		LIMIT $1
	`

	rows, err := db.Query(query, limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch prediction history"})
		return
	}
	defer rows.Close()

	var predictions []PredictionHistory

	for rows.Next() {
		var p PredictionHistory
		var insights pq.StringArray

		err := rows.Scan(
			&p.ID,
			&p.MatchID,
			&p.PredictedAt,
			&p.TeamAName,
			&p.TeamBName,
			&p.PredictedTeamAGoals,
			&p.PredictedTeamBGoals,
			&p.PredictedOutcome,
			&p.PredictedWinner,
			&p.ConfidenceScore,
			&p.ActualTeamAGoals,
			&p.ActualTeamBGoals,
			&p.ActualOutcome,
			&p.ActualWinner,
			&p.PredictionCorrect,
			&insights,
			&p.ModelVersion,
			&p.GoalsErrorTeamA,
			&p.GoalsErrorTeamB,
			&p.MatchDate,
		)

		if err != nil {
			continue
		}

		p.Insights = insights
		predictions = append(predictions, p)
	}

	c.JSON(http.StatusOK, gin.H{
		"predictions": predictions,
		"total":       len(predictions),
	})
}

// SavePrediction saves a prediction to history
func SavePrediction(db *sql.DB, matchID int, teamAName, teamBName string, mlResponse map[string]interface{}) error {
	query := `
		INSERT INTO prediction_history (
			match_id,
			team_a_name,
			team_b_name,
			predicted_team_a_goals,
			predicted_team_b_goals,
			predicted_outcome,
			predicted_winner,
			confidence_score,
			insights_generated,
			model_version,
			features_used
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
		ON CONFLICT (match_id) DO UPDATE SET
			predicted_team_a_goals = EXCLUDED.predicted_team_a_goals,
			predicted_team_b_goals = EXCLUDED.predicted_team_b_goals,
			predicted_outcome = EXCLUDED.predicted_outcome,
			predicted_winner = EXCLUDED.predicted_winner,
			confidence_score = EXCLUDED.confidence_score,
			insights_generated = EXCLUDED.insights_generated,
			model_version = EXCLUDED.model_version,
			features_used = EXCLUDED.features_used,
			predicted_at = CURRENT_TIMESTAMP
	`

	// Extract values from ML response
	teamAGoals := mlResponse["team_a_predicted_goals"]
	teamBGoals := mlResponse["team_b_predicted_goals"]
	outcome := mlResponse["predicted_outcome"]
	winner := mlResponse["predicted_winner"]
	confidence := mlResponse["confidence_score"]
	modelVersion := mlResponse["model_version"]

	// Extract insights
	var insights pq.StringArray
	if insightsRaw, ok := mlResponse["insights"].([]interface{}); ok {
		for _, insight := range insightsRaw {
			if str, ok := insight.(string); ok {
				insights = append(insights, str)
			}
		}
	}

	// Convert features to JSON
	featuresJSON, _ := json.Marshal(mlResponse["key_features"])

	_, err := db.Exec(query,
		matchID,
		teamAName,
		teamBName,
		teamAGoals,
		teamBGoals,
		outcome,
		winner,
		confidence,
		insights,
		modelVersion,
		featuresJSON,
	)

	return err
}

// UpdatePredictionWithActual updates prediction with actual match result
func UpdatePredictionWithActual(db *sql.DB, matchID int) error {
	query := `
		UPDATE prediction_history ph
		SET 
			actual_team_a_goals = m.home_score,
			actual_team_b_goals = m.away_score,
			actual_outcome = CASE 
				WHEN m.winner = 'HOME_TEAM' THEN ht.name || ' Win'
				WHEN m.winner = 'AWAY_TEAM' THEN at.name || ' Win'
				ELSE 'Draw'
			END,
			actual_winner = CASE 
				WHEN m.winner = 'HOME_TEAM' THEN ht.name
				WHEN m.winner = 'AWAY_TEAM' THEN at.name
				ELSE 'Draw'
			END,
			prediction_correct = (
				CASE 
					WHEN ph.predicted_winner = ht.name AND m.winner = 'HOME_TEAM' THEN true
					WHEN ph.predicted_winner = at.name AND m.winner = 'AWAY_TEAM' THEN true
					WHEN ph.predicted_winner = 'Draw' AND m.winner = 'DRAW' THEN true
					ELSE false
				END
			),
			goals_error_team_a = ABS(ph.predicted_team_a_goals - m.home_score),
			goals_error_team_b = ABS(ph.predicted_team_b_goals - m.away_score),
			updated_at = CURRENT_TIMESTAMP
		FROM matches m
		JOIN teams ht ON m.home_team_id = ht.id
		JOIN teams at ON m.away_team_id = at.id
		WHERE ph.match_id = m.id
		  AND ph.match_id = $1
		  AND m.status = 'FINISHED'
		  AND m.home_score IS NOT NULL
	`

	_, err := db.Exec(query, matchID)
	return err
}

// GetPredictionAccuracy returns overall prediction accuracy stats
func GetPredictionAccuracy(c *gin.Context, db *sql.DB) {
	query := `
		SELECT 
			COUNT(*) as total_predictions,
			SUM(CASE WHEN prediction_correct = true THEN 1 ELSE 0 END) as correct_predictions,
			AVG(goals_error_team_a) as avg_goals_error_a,
			AVG(goals_error_team_b) as avg_goals_error_b,
			AVG(confidence_score) as avg_confidence
		FROM prediction_history
		WHERE actual_team_a_goals IS NOT NULL
	`

	var stats struct {
		TotalPredictions   int     `json:"totalPredictions"`
		CorrectPredictions int     `json:"correctPredictions"`
		AvgGoalsErrorA     float64 `json:"avgGoalsErrorA"`
		AvgGoalsErrorB     float64 `json:"avgGoalsErrorB"`
		AvgConfidence      float64 `json:"avgConfidence"`
		AccuracyPercentage float64 `json:"accuracyPercentage"`
	}

	err := db.QueryRow(query).Scan(
		&stats.TotalPredictions,
		&stats.CorrectPredictions,
		&stats.AvgGoalsErrorA,
		&stats.AvgGoalsErrorB,
		&stats.AvgConfidence,
	)

	if err != nil {
		// If no data exists, return zeros instead of error
		if err == sql.ErrNoRows {
			c.JSON(http.StatusOK, gin.H{
				"totalPredictions":   0,
				"correctPredictions": 0,
				"avgGoalsErrorA":     0.0,
				"avgGoalsErrorB":     0.0,
				"avgConfidence":      0.0,
				"accuracyPercentage": 0.0,
			})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch accuracy stats"})
		return
	}

	if stats.TotalPredictions > 0 {
		stats.AccuracyPercentage = (float64(stats.CorrectPredictions) / float64(stats.TotalPredictions)) * 100
	}

	c.JSON(http.StatusOK, stats)
}
