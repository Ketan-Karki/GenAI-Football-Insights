package football

import "time"

// Competition represents a football competition/league
type Competition struct {
	ID            int     `json:"id"`
	Name          string  `json:"name"`
	Code          string  `json:"code"`
	Type          string  `json:"type"`
	Emblem        string  `json:"emblem"`
	CurrentSeason *Season `json:"currentSeason"`
	Area          Area    `json:"area"`
}

type Area struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
	Code string `json:"code"`
	Flag string `json:"flag"`
}

type Season struct {
	ID              int    `json:"id"`
	StartDate       string `json:"startDate"`
	EndDate         string `json:"endDate"`
	CurrentMatchday int    `json:"currentMatchday"`
}

// Match represents a football match
type Match struct {
	ID          int         `json:"id"`
	Competition Competition `json:"competition"`
	Season      Season      `json:"season"`
	UtcDate     time.Time   `json:"utcDate"`
	Status      string      `json:"status"`
	Matchday    int         `json:"matchday"`
	HomeTeam    Team        `json:"homeTeam"`
	AwayTeam    Team        `json:"awayTeam"`
	Score       Score       `json:"score"`
	Goals       []Goal      `json:"goals"`
	Referees    []Referee   `json:"referees"`
}

type Goal struct {
	Minute     int        `json:"minute"`
	InjuryTime *int       `json:"injuryTime"`
	Type       string     `json:"type"`
	Team       TeamRef    `json:"team"`
	Scorer     PlayerRef  `json:"scorer"`
	Assist     *PlayerRef `json:"assist"`
	Score      GoalScore  `json:"score"`
}

type TeamRef struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type PlayerRef struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

type GoalScore struct {
	Home int `json:"home"`
	Away int `json:"away"`
}

type Team struct {
	ID        int    `json:"id"`
	Name      string `json:"name"`
	ShortName string `json:"shortName"`
	TLA       string `json:"tla"`
	Crest     string `json:"crest"`
}

type Score struct {
	Winner   string    `json:"winner"`
	Duration string    `json:"duration"`
	FullTime ScoreTime `json:"fullTime"`
	HalfTime ScoreTime `json:"halfTime"`
}

type ScoreTime struct {
	Home *int `json:"home"`
	Away *int `json:"away"`
}

type Referee struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Type        string `json:"type"`
	Nationality string `json:"nationality"`
}

// Standing represents team standings in a competition
type Standing struct {
	Position       int    `json:"position"`
	Team           Team   `json:"team"`
	PlayedGames    int    `json:"playedGames"`
	Form           string `json:"form"`
	Won            int    `json:"won"`
	Draw           int    `json:"draw"`
	Lost           int    `json:"lost"`
	Points         int    `json:"points"`
	GoalsFor       int    `json:"goalsFor"`
	GoalsAgainst   int    `json:"goalsAgainst"`
	GoalDifference int    `json:"goalDifference"`
}

type StandingTable struct {
	Stage string     `json:"stage"`
	Type  string     `json:"type"`
	Group string     `json:"group,omitempty"`
	Table []Standing `json:"table"`
}

// API Response types
type CompetitionsResponse struct {
	Count        int           `json:"count"`
	Competitions []Competition `json:"competitions"`
}

type MatchesResponse struct {
	Filters struct {
		Season interface{} `json:"season"`
	} `json:"filters"`
	ResultSet struct {
		Count  int    `json:"count"`
		First  string `json:"first"`
		Last   string `json:"last"`
		Played int    `json:"played"`
	} `json:"resultSet"`
	Competition Competition `json:"competition"`
	Matches     []Match     `json:"matches"`
}

type StandingsResponse struct {
	Filters struct {
		Season interface{} `json:"season"`
	} `json:"filters"`
	Competition Competition     `json:"competition"`
	Season      Season          `json:"season"`
	Standings   []StandingTable `json:"standings"`
}

// Player represents a football player
type Player struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	FirstName   string `json:"firstName"`
	LastName    string `json:"lastName"`
	DateOfBirth string `json:"dateOfBirth"`
	Nationality string `json:"nationality"`
	Position    string `json:"position"`
	ShirtNumber *int   `json:"shirtNumber"`
}

// LineupPlayer represents a player in a match lineup with stats
type LineupPlayer struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Position    string `json:"position"`
	ShirtNumber int    `json:"shirtNumber"`
}

// Lineup represents team lineup for a match
type Lineup struct {
	Formation   string         `json:"formation"`
	StartXI     []LineupPlayer `json:"startXI"`
	Substitutes []LineupPlayer `json:"substitutes"`
	Coach       *Coach         `json:"coach"`
}

// Coach represents a team coach
type Coach struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Nationality string `json:"nationality"`
}

// MatchLineups represents the full lineup response for a match
type MatchLineups struct {
	HomeTeam struct {
		ID     int    `json:"id"`
		Name   string `json:"name"`
		Lineup Lineup `json:"lineup"`
	} `json:"homeTeam"`
	AwayTeam struct {
		ID     int    `json:"id"`
		Name   string `json:"name"`
		Lineup Lineup `json:"lineup"`
	} `json:"awayTeam"`
}

// TeamSquad represents a team's full squad
type TeamSquad struct {
	ID    int      `json:"id"`
	Name  string   `json:"name"`
	Squad []Player `json:"squad"`
}
