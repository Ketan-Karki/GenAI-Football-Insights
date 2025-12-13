package service

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/yourusername/football-prediction/internal/repository"
	"github.com/yourusername/football-prediction/pkg/cache"
	"github.com/yourusername/football-prediction/pkg/football"
)

type FootballService struct {
	client     *football.Client
	cache      *cache.Cache
	compRepo   *repository.CompetitionRepository
	matchRepo  *repository.MatchRepository
	playerRepo *repository.PlayerRepository
	cacheTTL   time.Duration
}

func NewFootballService(apiKey string, db *sql.DB) *FootballService {
	return &FootballService{
		client:     football.NewClient(apiKey),
		cache:      cache.New(),
		compRepo:   repository.NewCompetitionRepository(db),
		matchRepo:  repository.NewMatchRepository(db),
		playerRepo: repository.NewPlayerRepository(db),
		cacheTTL:   24 * time.Hour, // 24 hours cache
	}
}

func (s *FootballService) GetCompetitions() ([]football.Competition, error) {
	// Check cache first
	cacheKey := "competitions:all"
	if cached, found := s.cache.Get(cacheKey); found {
		return cached.([]football.Competition), nil
	}

	// Fetch from API
	resp, err := s.client.GetCompetitions()
	if err != nil {
		return nil, fmt.Errorf("failed to fetch competitions: %w", err)
	}

	// Save to database
	for i := range resp.Competitions {
		if err := s.compRepo.Create(&resp.Competitions[i]); err != nil {
			// Log error but continue
			fmt.Printf("Failed to save competition %s: %v\n", resp.Competitions[i].Code, err)
		}
	}

	// Cache the result
	s.cache.Set(cacheKey, resp.Competitions, s.cacheTTL)

	return resp.Competitions, nil
}

func (s *FootballService) GetMatches(competitionCode string, season string) (*football.MatchesResponse, error) {
	// Check cache
	cacheKey := fmt.Sprintf("matches:%s:%s", competitionCode, season)
	if cached, found := s.cache.Get(cacheKey); found {
		return cached.(*football.MatchesResponse), nil
	}

	// Fetch from API
	resp, err := s.client.GetMatches(competitionCode, season)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch matches: %w", err)
	}

	// Cache the result (shorter TTL for matches)
	s.cache.Set(cacheKey, resp, 12*time.Hour)

	return resp, nil
}

func (s *FootballService) GetStandings(competitionCode string, season string) (*football.StandingsResponse, error) {
	// Check cache
	cacheKey := fmt.Sprintf("standings:%s:%s", competitionCode, season)
	if cached, found := s.cache.Get(cacheKey); found {
		return cached.(*football.StandingsResponse), nil
	}

	// Fetch from API
	resp, err := s.client.GetStandings(competitionCode, season)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch standings: %w", err)
	}

	// Cache the result
	s.cache.Set(cacheKey, resp, s.cacheTTL)

	return resp, nil
}

func (s *FootballService) GetMatch(matchID int) (*football.Match, error) {
	// Check cache
	cacheKey := fmt.Sprintf("match:%d", matchID)
	if cached, found := s.cache.Get(cacheKey); found {
		return cached.(*football.Match), nil
	}

	// Fetch from API
	match, err := s.client.GetMatch(matchID)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch match: %w", err)
	}

	// Cache the result (shorter TTL for individual matches)
	s.cache.Set(cacheKey, match, 6*time.Hour)

	return match, nil
}

// GetHeadToHead returns historical record between the two clubs (by external team IDs).
func (s *FootballService) GetHeadToHead(homeTeamExternalID, awayTeamExternalID, limit int) (*repository.HeadToHeadRecord, error) {
	if s.matchRepo == nil {
		return nil, fmt.Errorf("match repository not initialised")
	}

	return s.matchRepo.GetHeadToHeadByExternalTeamIDs(homeTeamExternalID, awayTeamExternalID, limit)
}

// GetKeyPlayers returns key players for the given match, grouped into home/away
// based on the current fixture's team IDs. This is best-effort and may return
// empty slices if no stats are present yet.
func (s *FootballService) GetKeyPlayers(matchExternalID, homeTeamExternalID, awayTeamExternalID, limit int) (home, away []repository.PlayerInsight, err error) {
	if s.playerRepo == nil {
		return nil, nil, fmt.Errorf("player repository not initialised")
	}

	players, err := s.playerRepo.GetKeyPlayersForMatch(matchExternalID, limit)
	if err != nil {
		return nil, nil, err
	}

	for _, p := range players {
		if p.TeamExternalID == homeTeamExternalID {
			home = append(home, p)
		} else if p.TeamExternalID == awayTeamExternalID {
			away = append(away, p)
		}
	}

	return home, away, nil
}
