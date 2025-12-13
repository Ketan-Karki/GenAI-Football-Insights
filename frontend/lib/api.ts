const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export interface Competition {
  id: number;
  name: string;
  code: string;
  emblem?: string;
  area: {
    name: string;
    code: string;
  };
}

export interface Team {
  id: number;
  name: string;
  shortName: string;
  tla: string;
  crest: string;
}

export interface Match {
  id: number;
  utcDate: string;
  status: string;
  matchday: number;
  homeTeam: Team;
  awayTeam: Team;
  score: {
    winner: string | null;
    fullTime: {
      home: number | null;
      away: number | null;
    };
  };
  competition: Competition;
}

export interface TeamStats {
  homeForm: number;
  awayForm: number;
  homeGoalsAvg: number;
  awayGoalsAvg: number;
  homeWinRate: number;
  awayWinRate: number;
}

export interface HeadToHead {
  homeWins: number;
  awayWins: number;
  draws: number;
}

export interface PlayerInsight {
  name: string;
  position: string;
  teamExternalId: number;
  goals: number;
  assists: number;
  rating?: number | null;
}

export interface KeyPlayers {
  home: PlayerInsight[];
  away: PlayerInsight[];
}

export interface Prediction {
  matchId: number;
  homeTeam?: string;
  awayTeam?: string;
  homeWinProbability: number;
  drawProbability: number;
  awayWinProbability: number;
  predictedOutcome: string;
  predictedWinner?: string;
  confidenceScore: number;
  modelVersion?: string;
  modelAccuracy?: number;
  teamStats?: {
    homeForm: number;
    awayForm: number;
    homeGoalsAvg: number;
    awayGoalsAvg: number;
  };
  headToHead?: HeadToHead;
  ballKnowledge?: string[];
  insights?: string[];
  keyPlayers?: KeyPlayers;
}

export interface Standing {
  position: number;
  team: Team;
  playedGames: number;
  won: number;
  draw: number;
  lost: number;
  points: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  form: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }

  async getCompetitions(): Promise<{ competitions: Competition[] }> {
    return this.fetch("/api/v1/competitions");
  }

  async getMatches(
    competition: string,
    season?: string
  ): Promise<{ matches: Match[] }> {
    const params = new URLSearchParams({ competition });
    if (season) params.append("season", season);
    return this.fetch(`/api/v1/matches?${params}`);
  }

  async getMatch(id: number): Promise<Match> {
    return this.fetch(`/api/v1/matches/${id}`);
  }

  async getStandings(
    competition: string,
    season?: string
  ): Promise<{
    standings: Array<{ table: Standing[] }>;
  }> {
    const params = season ? `?season=${season}` : "";
    return this.fetch(`/api/v1/standings/${competition}${params}`);
  }

  async getPrediction(matchId: number): Promise<Prediction> {
    return this.fetch(`/api/v1/predictions/${matchId}`);
  }
}

export const api = new ApiClient(API_URL);
