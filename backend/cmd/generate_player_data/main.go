package main

import (
	"database/sql"
	"fmt"
	"log"
	"math/rand"
	"os"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

// Generate realistic player data based on actual match scores
// This creates demo data that looks authentic using real match results

type matchData struct {
	id         int
	externalID int
	homeTeamID int
	awayTeamID int
	homeName   string
	awayName   string
	homeScore  int
	awayScore  int
}

func main() {
	_ = godotenv.Load()
	_ = godotenv.Load("../.env")
	_ = godotenv.Load("../../.env")

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL not set")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}
	defer db.Close()

	rand.Seed(time.Now().UnixNano())

	fmt.Println("🔄 Generating realistic player data from match scores...")

	// Get recent finished matches with scores
	rows, err := db.Query(`
		SELECT m.id, m.external_id, m.home_team_id, m.away_team_id,
		       ht.name as home_name, at.name as away_name,
		       m.home_score, m.away_score
		FROM matches m
		JOIN teams ht ON m.home_team_id = ht.id
		JOIN teams at ON m.away_team_id = at.id
		WHERE m.status = 'FINISHED' 
		  AND m.home_score IS NOT NULL
		  AND m.away_score IS NOT NULL
		  AND m.utc_date >= NOW() - INTERVAL '30 days'
		ORDER BY m.utc_date DESC
		LIMIT 20
	`)
	if err != nil {
		log.Fatalf("failed to query matches: %v", err)
	}
	defer rows.Close()

	var matches []matchData
	for rows.Next() {
		var m matchData
		if err := rows.Scan(&m.id, &m.externalID, &m.homeTeamID, &m.awayTeamID,
			&m.homeName, &m.awayName, &m.homeScore, &m.awayScore); err != nil {
			log.Printf("Failed to scan: %v", err)
			continue
		}
		matches = append(matches, m)
	}

	fmt.Printf("Found %d matches with scores\n", len(matches))

	successCount := 0
	for i, match := range matches {
		fmt.Printf("[%d/%d] %s %d-%d %s\n", i+1, len(matches),
			match.homeName, match.homeScore, match.awayScore, match.awayName)

		// Check if already has data
		var existing int
		db.QueryRow(`SELECT COUNT(*) FROM player_match_stats WHERE match_id = $1`, match.id).Scan(&existing)
		if existing > 0 {
			fmt.Println("  ⏭️  Already has player data")
			continue
		}

		// Generate realistic player data
		if err := generatePlayersForMatch(db, match); err != nil {
			log.Printf("  ⚠️  Failed: %v", err)
			continue
		}

		successCount++
		fmt.Println("  ✅ Generated player data")
	}

	fmt.Printf("\n✅ Complete! Generated data for %d matches\n", successCount)
}

func generatePlayersForMatch(db *sql.DB, match matchData) error {
	// Generate home team players
	if match.homeScore > 0 {
		if err := generateTeamPlayers(db, match.id, match.homeTeamID, match.homeName, match.homeScore, true); err != nil {
			return err
		}
	}

	// Generate away team players
	if match.awayScore > 0 {
		if err := generateTeamPlayers(db, match.id, match.awayTeamID, match.awayName, match.awayScore, false); err != nil {
			return err
		}
	}

	return nil
}

func generateTeamPlayers(db *sql.DB, matchID, teamID int, teamName string, goals int, isHome bool) error {
	// Realistic player names for different positions
	strikerNames := []string{"Silva", "Martinez", "Johnson", "Fernandez", "Anderson", "Wilson", "Garcia", "Rodriguez"}
	midfielderNames := []string{"Smith", "Brown", "Davis", "Miller", "Moore", "Taylor", "Thomas", "Jackson"}

	// Distribute goals among players (1-2 players typically score)
	scorers := make(map[string]int)
	assists := make(map[string]int)

	// Primary scorer gets most goals
	if goals > 0 {
		primaryScorer := strikerNames[rand.Intn(len(strikerNames))]
		if goals == 1 {
			scorers[primaryScorer] = 1
		} else {
			scorers[primaryScorer] = goals - rand.Intn(2) // 1-2 goals for primary
			if scorers[primaryScorer] < goals {
				// Secondary scorer
				secondaryScorer := strikerNames[rand.Intn(len(strikerNames))]
				for secondaryScorer == primaryScorer {
					secondaryScorer = strikerNames[rand.Intn(len(strikerNames))]
				}
				scorers[secondaryScorer] = goals - scorers[primaryScorer]
			}
		}

		// Generate assists (60% of goals have assists)
		assistCount := int(float64(goals) * 0.6)
		for i := 0; i < assistCount; i++ {
			assister := midfielderNames[rand.Intn(len(midfielderNames))]
			assists[assister]++
		}
	}

	// Insert players
	playerID := 1000000 + matchID*100 + teamID // Generate unique external IDs

	for name, goalCount := range scorers {
		assistCount := assists[name]

		var dbPlayerID int
		err := db.QueryRow(`
			INSERT INTO players (external_id, name, position, team_id)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (external_id) DO UPDATE SET name = EXCLUDED.name
			RETURNING id
		`, playerID, name, "Attacker", teamID).Scan(&dbPlayerID)
		if err != nil {
			return fmt.Errorf("failed to insert player: %w", err)
		}

		_, err = db.Exec(`
			INSERT INTO player_match_stats (match_id, player_id, goals, assists)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (match_id, player_id) DO UPDATE SET
				goals = EXCLUDED.goals, assists = EXCLUDED.assists
		`, matchID, dbPlayerID, goalCount, assistCount)
		if err != nil {
			return fmt.Errorf("failed to insert stats: %w", err)
		}

		playerID++
	}

	// Insert assist-only players
	for name, assistCount := range assists {
		if _, exists := scorers[name]; exists {
			continue // Already inserted
		}

		var dbPlayerID int
		err := db.QueryRow(`
			INSERT INTO players (external_id, name, position, team_id)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (external_id) DO UPDATE SET name = EXCLUDED.name
			RETURNING id
		`, playerID, name, "Midfielder", teamID).Scan(&dbPlayerID)
		if err != nil {
			return fmt.Errorf("failed to insert player: %w", err)
		}

		_, err = db.Exec(`
			INSERT INTO player_match_stats (match_id, player_id, goals, assists)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (match_id, player_id) DO UPDATE SET
				goals = EXCLUDED.goals, assists = EXCLUDED.assists
		`, matchID, dbPlayerID, 0, assistCount)
		if err != nil {
			return fmt.Errorf("failed to insert stats: %w", err)
		}

		playerID++
	}

	return nil
}
