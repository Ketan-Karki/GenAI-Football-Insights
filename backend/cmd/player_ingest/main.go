package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/yourusername/football-prediction/pkg/football"
)

// This command ingests player goal/assist data from football-data.org
// for recent finished matches into the local Postgres database.
// Uses the FREE tier goals endpoint which includes scorer and assist information.

func main() {
	// Load .env
	_ = godotenv.Load()
	_ = godotenv.Load("../.env")
	_ = godotenv.Load("../../.env")

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL not set")
	}

	apiKey := os.Getenv("FOOTBALL_DATA_API_KEY")
	if apiKey == "" {
		log.Fatal("FOOTBALL_DATA_API_KEY not set")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatalf("failed to ping database: %v", err)
	}

	client := football.NewClient(apiKey)

	fmt.Println("🔄 Starting player data ingestion...")
	fmt.Println("   📊 Using football-data.org goals data (FREE tier)")
	fmt.Println("   ⚠️  Rate limit: 10 requests/minute")
	fmt.Println("   Fetching recent finished matches from database...")

	// Get recent finished matches from last 30 days
	// Limit to 10 matches to respect rate limits
	cutoffDate := time.Now().AddDate(0, 0, -30)
	rows, err := db.Query(`
        SELECT m.id, m.external_id, m.home_team_id, m.away_team_id
        FROM matches m
        WHERE m.status = 'FINISHED' 
          AND m.utc_date >= $1
          AND m.utc_date < NOW()
        ORDER BY m.utc_date DESC
        LIMIT 10
    `, cutoffDate)
	if err != nil {
		log.Fatalf("failed to query matches: %v", err)
	}
	defer rows.Close()

	type matchRecord struct {
		id         int
		externalID int
		homeTeamID int
		awayTeamID int
	}

	var matches []matchRecord
	for rows.Next() {
		var m matchRecord
		if err := rows.Scan(&m.id, &m.externalID, &m.homeTeamID, &m.awayTeamID); err != nil {
			log.Printf("⚠️  Failed to scan match: %v", err)
			continue
		}
		matches = append(matches, m)
	}

	fmt.Printf("   Found %d finished matches to process\n", len(matches))

	successCount := 0
	skipCount := 0

	for i, match := range matches {
		fmt.Printf("   [%d/%d] Processing match %d...\n", i+1, len(matches), match.externalID)

		// Check if we already have player stats for this match
		var existingCount int
		err := db.QueryRow(`
            SELECT COUNT(*) FROM player_match_stats WHERE match_id = $1
        `, match.id).Scan(&existingCount)
		if err != nil {
			log.Printf("⚠️  Failed to check existing stats: %v", err)
			continue
		}

		if existingCount > 0 {
			fmt.Printf("      ⏭️  Skipping (already have player stats)\n")
			skipCount++
			continue
		}

		// Fetch match details with goals from football-data.org
		matchDetails, err := client.GetMatch(match.externalID)
		if err != nil {
			log.Printf("⚠️  Failed to fetch match %d: %v", match.externalID, err)
			continue
		}

		if len(matchDetails.Goals) == 0 {
			fmt.Printf("      ⏭️  No goals in match\n")
			skipCount++
			continue
		}

		// Process goals and assists
		if err := processMatchGoals(db, match.id, match.homeTeamID, match.awayTeamID, matchDetails.Goals); err != nil {
			log.Printf("⚠️  Failed to process goals: %v", err)
			continue
		}

		successCount++
		fmt.Printf("      ✅ Processed lineups\n")

		// Rate limiting: 10 requests per minute
		if i < len(matches)-1 {
			fmt.Printf("      ⏳ Waiting 6 seconds (rate limit)...\n")
			time.Sleep(6 * time.Second)
		}
	}

	fmt.Printf("\n✅ Player ingestion complete!\n")
	fmt.Printf("   Processed: %d matches\n", successCount)
	fmt.Printf("   Skipped: %d matches (already had data)\n", skipCount)
}

func processMatchGoals(db *sql.DB, matchID, homeTeamID, awayTeamID int, goals []football.Goal) error {
	// Build player stats map from goals
	playerStats := make(map[int]struct {
		goals   int
		assists int
		teamID  int
		name    string
	})

	for _, goal := range goals {
		// Determine team ID
		teamID := homeTeamID
		if goal.Team.ID != 0 {
			// Check if it's away team
			var awayExtID int
			db.QueryRow(`SELECT external_id FROM teams WHERE id = $1`, awayTeamID).Scan(&awayExtID)
			if goal.Team.ID == awayExtID {
				teamID = awayTeamID
			}
		}

		// Count goal for scorer
		if goal.Scorer.ID > 0 {
			stats := playerStats[goal.Scorer.ID]
			stats.goals++
			stats.teamID = teamID
			stats.name = goal.Scorer.Name
			playerStats[goal.Scorer.ID] = stats
		}

		// Count assist
		if goal.Assist != nil && goal.Assist.ID > 0 {
			stats := playerStats[goal.Assist.ID]
			stats.assists++
			stats.teamID = teamID
			stats.name = goal.Assist.Name
			playerStats[goal.Assist.ID] = stats
		}
	}

	// Insert players and stats
	for extID, stats := range playerStats {
		// Upsert player
		var playerID int
		err := db.QueryRow(`
            INSERT INTO players (external_id, name, team_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (external_id) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = NOW()
            RETURNING id
        `, extID, stats.name, stats.teamID).Scan(&playerID)
		if err != nil {
			log.Printf("⚠️  Failed to upsert player %s: %v", stats.name, err)
			continue
		}

		// Insert player match stats
		_, err = db.Exec(`
            INSERT INTO player_match_stats (match_id, player_id, goals, assists)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (match_id, player_id) DO UPDATE SET
                goals = EXCLUDED.goals,
                assists = EXCLUDED.assists
        `, matchID, playerID, stats.goals, stats.assists)
		if err != nil {
			log.Printf("⚠️  Failed to insert player stats: %v", err)
		}
	}

	fmt.Printf("      ✅ Processed %d players (%d goals)\n", len(playerStats), len(goals))
	return nil
}
