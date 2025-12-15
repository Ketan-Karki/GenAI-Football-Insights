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

func main() {
	// Load environment variables from project root
	if err := godotenv.Load("../.env"); err != nil {
		// Try two levels up
		if err := godotenv.Load("../../.env"); err != nil {
			log.Println("No .env file found, using environment variables")
		}
	}

	// Get API key
	apiKey := os.Getenv("FOOTBALL_API_KEY")
	if apiKey == "" {
		log.Fatal("FOOTBALL_API_KEY not set")
	}

	// Connect to database
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL not set")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatal("Failed to ping database:", err)
	}

	log.Println("✅ Connected to database")

	// Create API client
	client := football.NewClient(apiKey)

	// Competitions to ingest
	// Club competitions: PL (Premier League), PD (La Liga), BL1 (Bundesliga), SA (Serie A), FL1 (Ligue 1), CL (Champions League)
	// International: WC (World Cup), QCAF (CAF Qualifiers), QAFC (AFC Qualifiers), QUFA (UEFA Qualifiers),
	//                QOFC (OFC Qualifiers), QCBL (CONMEBOL Qualifiers), UNL (UEFA Nations League),
	//                ECQ (Euro Qualifiers), EC (European Championship), CA (Copa America)
	competitions := []string{"PL", "PD", "BL1", "SA", "FL1", "CL", "WC", "QCAF", "QAFC", "QUFA", "QOFC", "QCBL", "UNL", "ECQ", "EC", "CA"}
	seasons := []string{"2024", "2025"}

	log.Println("🚀 Starting data ingestion...")

	for _, comp := range competitions {
		for _, season := range seasons {
			log.Printf("📥 Fetching %s season %s...", comp, season)

			// Fetch matches with retry on rate limit
			var matches *football.MatchesResponse
			var err error

			for retries := 0; retries < 3; retries++ {
				matches, err = client.GetMatches(comp, season)
				if err == nil {
					break
				}

				// Check if it's a rate limit error
				if err != nil && (err.Error() == "API error (status 429)" ||
					err.Error() == "failed to parse response: json: cannot unmarshal number into Go struct field .filters.season of type string") {
					log.Printf("⏳ Rate limit hit, waiting 60 seconds...")
					time.Sleep(60 * time.Second)
					continue
				}

				log.Printf("❌ Error fetching %s %s: %v", comp, season, err)
				break
			}

			if err != nil {
				continue
			}

			if matches == nil || len(matches.Matches) == 0 {
				log.Printf("⚠️  No matches found for %s %s", comp, season)
				time.Sleep(7 * time.Second)
				continue
			}

			// Save competition
			if err := saveCompetition(db, &matches.Competition); err != nil {
				log.Printf("❌ Error saving competition: %v", err)
				continue
			}

			// Save matches
			saved := 0
			for _, match := range matches.Matches {
				if err := saveMatch(db, &match); err != nil {
					log.Printf("❌ Error saving match %d: %v", match.ID, err)
					continue
				}
				saved++
			}

			log.Printf("✅ Saved %d/%d matches for %s %s", saved, len(matches.Matches), comp, season)

			// Rate limiting - API allows 10 req/min
			time.Sleep(7 * time.Second)
		}
	}

	log.Println("🎉 Data ingestion complete!")
}

func saveCompetition(db *sql.DB, comp *football.Competition) error {
	query := `
		INSERT INTO competitions (external_id, name, code, area_name, current_season_start_date, current_season_end_date)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (external_id) DO UPDATE
		SET name = EXCLUDED.name,
		    code = EXCLUDED.code,
		    area_name = EXCLUDED.area_name,
		    updated_at = CURRENT_TIMESTAMP
	`

	var startDate, endDate *string
	if comp.CurrentSeason != nil {
		startDate = &comp.CurrentSeason.StartDate
		endDate = &comp.CurrentSeason.EndDate
	}

	_, err := db.Exec(query, comp.ID, comp.Name, comp.Code, comp.Area.Name, startDate, endDate)
	return err
}

func saveMatch(db *sql.DB, match *football.Match) error {
	// Save home team
	if err := saveTeam(db, &match.HomeTeam); err != nil {
		return fmt.Errorf("failed to save home team: %w", err)
	}

	// Save away team
	if err := saveTeam(db, &match.AwayTeam); err != nil {
		return fmt.Errorf("failed to save away team: %w", err)
	}

	// Save match
	query := `
		INSERT INTO matches (
			external_id, competition_id, season, home_team_id, away_team_id,
			utc_date, status, matchday, home_score, away_score, winner
		)
		SELECT $1, c.id, $2, ht.id, at.id, $3, $4, $5, $6, $7, $8
		FROM competitions c
		CROSS JOIN teams ht
		CROSS JOIN teams at
		WHERE c.external_id = $9
		  AND ht.external_id = $10
		  AND at.external_id = $11
		ON CONFLICT (external_id) DO UPDATE
		SET status = EXCLUDED.status,
		    home_score = EXCLUDED.home_score,
		    away_score = EXCLUDED.away_score,
		    winner = EXCLUDED.winner,
		    updated_at = CURRENT_TIMESTAMP
	`

	var homeScore, awayScore *int
	if match.Score.FullTime.Home != nil {
		homeScore = match.Score.FullTime.Home
	}
	if match.Score.FullTime.Away != nil {
		awayScore = match.Score.FullTime.Away
	}

	var winner *string
	if match.Score.Winner != "" {
		winner = &match.Score.Winner
	}

	// Get season from match
	season := fmt.Sprintf("%d", match.Season.ID)

	_, err := db.Exec(
		query,
		match.ID,             // $1 external_id
		season,               // $2 season
		match.UtcDate,        // $3 utc_date
		match.Status,         // $4 status
		match.Matchday,       // $5 matchday
		homeScore,            // $6 home_score
		awayScore,            // $7 away_score
		winner,               // $8 winner
		match.Competition.ID, // $9 competition external_id
		match.HomeTeam.ID,    // $10 home_team external_id
		match.AwayTeam.ID,    // $11 away_team external_id
	)

	return err
}

func saveTeam(db *sql.DB, team *football.Team) error {
	query := `
		INSERT INTO teams (external_id, name, short_name, tla, crest_url)
		VALUES ($1, $2, $3, $4, $5)
		ON CONFLICT (external_id) DO UPDATE
		SET name = EXCLUDED.name,
		    short_name = EXCLUDED.short_name,
		    tla = EXCLUDED.tla,
		    crest_url = EXCLUDED.crest_url,
		    updated_at = CURRENT_TIMESTAMP
	`

	_, err := db.Exec(query, team.ID, team.Name, team.ShortName, team.TLA, team.Crest)
	return err
}
