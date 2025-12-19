"use client";

import { useEffect, useState } from "react";
import { api, type Match } from "@/lib/api";
import { MatchCard } from "./match-card";
import { Button } from "./ui/button";
import { useMatchContext } from "@/contexts/MatchContext";

const COMPETITIONS = [
  { code: "PL", name: "Premier League", emoji: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
  { code: "PD", name: "La Liga", emoji: "🇪🇸" },
  { code: "BL1", name: "Bundesliga", emoji: "🇩🇪" },
  { code: "SA", name: "Serie A", emoji: "🇮🇹" },
  { code: "FL1", name: "Ligue 1", emoji: "🇫🇷" },
  { code: "CL", name: "Champions League", emoji: "🏆" },
  { code: "WC", name: "World Cup", emoji: "🌍" },
];

export function MatchList() {
  const { getMatches, setMatches: cacheMatches } = useMatchContext();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState("PL");

  useEffect(() => {
    async function fetchMatches() {
      try {
        setLoading(true);
        setError(null);

        // Check cache first
        const cachedMatches = getMatches(selectedCompetition);
        if (cachedMatches && cachedMatches.length > 0) {
          setMatches(cachedMatches);
          setLoading(false);
          return;
        }

        const data = await api.getMatches(selectedCompetition);

        // Filter for upcoming matches
        const now = new Date();
        // Use 180 days for cup competitions (World Cup, Champions League)
        const daysAhead = ["WC", "CL"].includes(selectedCompetition) ? 180 : 30;
        const futureDate = new Date(
          now.getTime() + daysAhead * 24 * 60 * 60 * 1000
        );

        const upcomingMatches = (data.matches || []).filter((match) => {
          const matchDate = new Date(match.utcDate);
          // Filter out matches with placeholder teams (id: 0)
          const hasValidTeams =
            match.homeTeam.id !== 0 && match.awayTeam.id !== 0;

          return (
            (match.status === "SCHEDULED" || match.status === "TIMED") &&
            matchDate >= now &&
            matchDate <= futureDate &&
            hasValidTeams
          );
        });

        // Sort by date (earliest first)
        upcomingMatches.sort(
          (a, b) =>
            new Date(a.utcDate).getTime() - new Date(b.utcDate).getTime()
        );

        setMatches(upcomingMatches);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch matches"
        );
        console.error("Error fetching matches:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchMatches();
  }, [selectedCompetition]);

  return (
    <div className="space-y-6">
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {COMPETITIONS.map((comp) => (
          <Button
            key={comp.code}
            variant={selectedCompetition === comp.code ? "default" : "outline"}
            onClick={() => setSelectedCompetition(comp.code)}
            className="whitespace-nowrap gap-2"
          >
            <span>{comp.emoji}</span>
            <span>{comp.name}</span>
          </Button>
        ))}
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-slate-600 dark:text-slate-400">
            Loading matches...
          </p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg p-4 text-center">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            Make sure the backend API is running on http://localhost:8080
          </p>
        </div>
      )}

      {!loading && !error && matches.length === 0 && (
        <div className="bg-[#2B3139] border border-border rounded-lg p-12 text-center">
          <div className="text-6xl mb-4">⚽</div>
          <h3 className="text-xl font-bold text-foreground mb-2">
            No Upcoming Matches
          </h3>
          <p className="text-[#848E9C] text-sm">
            {["WC", "CL"].includes(selectedCompetition)
              ? "No confirmed matches in the next 6 months for this competition."
              : "No scheduled matches in the next 30 days for this competition."}
          </p>
          <p className="text-[#848E9C] text-sm mt-2">
            Try selecting a different league above.
          </p>
        </div>
      )}

      {!loading && !error && matches.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {matches.slice(0, 12).map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  );
}
