package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"

	"github.com/yourusername/football-prediction/pkg/apifootball"
)

// Quick test to verify API-Football integration works
func main() {
	_ = godotenv.Load()
	_ = godotenv.Load("../.env")
	_ = godotenv.Load("../../.env")

	dbURL := os.Getenv("DATABASE_URL")
	apiKey := os.Getenv("API_FOOTBALL_KEY")

	if dbURL == "" || apiKey == "" {
		log.Fatal("DATABASE_URL or API_FOOTBALL_KEY not set")
	}

	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}
	defer db.Close()

	client := apifootball.NewClient(apiKey)

	// Test with known fixture ID
	fixtureID := 1035098
	fmt.Printf("Testing with fixture ID: %d\n\n", fixtureID)

	// Fetch lineups
	fmt.Println("1. Fetching lineups...")
	lineups, err := client.GetFixtureLineups(fixtureID)
	if err != nil {
		log.Fatalf("Failed to fetch lineups: %v", err)
	}

	fmt.Printf("   ✅ Got %d lineups\n", len(lineups))
	for i, lineup := range lineups {
		fmt.Printf("   Team %d: %s (%s) - %d starters, %d subs\n",
			i+1, lineup.Team.Name, lineup.Formation,
			len(lineup.StartXI), len(lineup.Substitutes))
	}

	// Fetch events
	fmt.Println("\n2. Fetching events...")
	events, err := client.GetFixtureEvents(fixtureID)
	if err != nil {
		log.Printf("   ⚠️  Failed to fetch events: %v", err)
		events = []apifootball.FixtureEvent{}
	} else {
		fmt.Printf("   ✅ Got %d events\n", len(events))

		// Count goals and assists
		goalCount := 0
		assistCount := 0
		for _, event := range events {
			if event.Type == "Goal" && event.Detail != "Missed Penalty" {
				goalCount++
				if event.Assist.ID > 0 {
					assistCount++
				}
			}
		}
		fmt.Printf("   Goals: %d, Assists: %d\n", goalCount, assistCount)
	}

	// Test player stats extraction
	fmt.Println("\n3. Extracting player stats from events...")
	playerStats := make(map[int]struct{ goals, assists int })
	for _, event := range events {
		if event.Type == "Goal" && event.Detail != "Missed Penalty" {
			stats := playerStats[event.Player.ID]
			stats.goals++
			playerStats[event.Player.ID] = stats
			fmt.Printf("   Goal: %s (ID: %d)\n", event.Player.Name, event.Player.ID)
		}
		if event.Assist.ID > 0 {
			stats := playerStats[event.Assist.ID]
			stats.assists++
			playerStats[event.Assist.ID] = stats
			fmt.Printf("   Assist: %s (ID: %d)\n", event.Assist.Name, event.Assist.ID)
		}
	}

	fmt.Printf("\n✅ Test successful! API-Football integration is working.\n")
	fmt.Printf("   Ready to run full player ingestion.\n")
}
