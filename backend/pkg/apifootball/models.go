package apifootball

// API-Football response wrapper
type Response struct {
	Get        string      `json:"get"`
	Parameters interface{} `json:"parameters"`
	Errors     []string    `json:"errors"`
	Results    int         `json:"results"`
	Paging     Paging      `json:"paging"`
	Response   interface{} `json:"response"`
}

type Paging struct {
	Current int `json:"current"`
	Total   int `json:"total"`
}

// Fixture lineup response
type FixtureLineupsResponse struct {
	Team        TeamInfo       `json:"team"`
	Formation   string         `json:"formation"`
	StartXI     []LineupPlayer `json:"startXI"`
	Substitutes []LineupPlayer `json:"substitutes"`
	Coach       Coach          `json:"coach"`
}

type TeamInfo struct {
	ID     int    `json:"id"`
	Name   string `json:"name"`
	Logo   string `json:"logo"`
	Colors Colors `json:"colors"`
}

type Colors struct {
	Player     ColorInfo `json:"player"`
	Goalkeeper ColorInfo `json:"goalkeeper"`
}

type ColorInfo struct {
	Primary string `json:"primary"`
	Number  string `json:"number"`
	Border  string `json:"border"`
}

type LineupPlayer struct {
	Player PlayerInfo `json:"player"`
}

type PlayerInfo struct {
	ID     int    `json:"id"`
	Name   string `json:"name"`
	Number int    `json:"number"`
	Pos    string `json:"pos"`
	Grid   string `json:"grid"`
}

type Coach struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Photo string `json:"photo"`
}

// Player statistics response
type PlayerStatsResponse struct {
	Player     PlayerDetails `json:"player"`
	Statistics []Statistics  `json:"statistics"`
}

type PlayerDetails struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	Firstname   string `json:"firstname"`
	Lastname    string `json:"lastname"`
	Age         int    `json:"age"`
	Birth       Birth  `json:"birth"`
	Nationality string `json:"nationality"`
	Height      string `json:"height"`
	Weight      string `json:"weight"`
	Photo       string `json:"photo"`
}

type Birth struct {
	Date    string `json:"date"`
	Place   string `json:"place"`
	Country string `json:"country"`
}

type Statistics struct {
	Team    TeamInfo   `json:"team"`
	League  LeagueInfo `json:"league"`
	Games   Games      `json:"games"`
	Goals   Goals      `json:"goals"`
	Passes  Passes     `json:"passes"`
	Shots   Shots      `json:"shots"`
	Tackles Tackles    `json:"tackles"`
}

type LeagueInfo struct {
	ID      int    `json:"id"`
	Name    string `json:"name"`
	Country string `json:"country"`
	Logo    string `json:"logo"`
	Flag    string `json:"flag"`
	Season  int    `json:"season"`
}

type Games struct {
	Appearences int    `json:"appearences"`
	Lineups     int    `json:"lineups"`
	Minutes     int    `json:"minutes"`
	Number      int    `json:"number"`
	Position    string `json:"position"`
	Rating      string `json:"rating"`
	Captain     bool   `json:"captain"`
}

type Goals struct {
	Total   int `json:"total"`
	Assists int `json:"assists"`
	Saves   int `json:"saves"`
}

type Passes struct {
	Total    int    `json:"total"`
	Key      int    `json:"key"`
	Accuracy string `json:"accuracy"`
}

type Shots struct {
	Total int `json:"total"`
	On    int `json:"on"`
}

type Tackles struct {
	Total         int `json:"total"`
	Blocks        int `json:"blocks"`
	Interceptions int `json:"interceptions"`
}

// Fixture events response (for goals/assists)
type FixtureEvent struct {
	Time   TimeInfo   `json:"time"`
	Team   TeamInfo   `json:"team"`
	Player PlayerInfo `json:"player"`
	Assist AssistInfo `json:"assist"`
	Type   string     `json:"type"`
	Detail string     `json:"detail"`
}

type TimeInfo struct {
	Elapsed int `json:"elapsed"`
	Extra   int `json:"extra"`
}

type AssistInfo struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}
