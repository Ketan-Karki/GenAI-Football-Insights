"use client";

import { useEffect, useState } from "react";
import { api, type Match } from "@/lib/api";
import { MatchCard } from "./match-card";
import { Button } from "./ui/button";

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
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState("PL");

  useEffect(() => {
    async function fetchMatches() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getMatches(selectedCompetition);

        // Filter for upcoming matches only (scheduled or in next 30 days)
        const now = new Date();
        const thirtyDaysFromNow = new Date(
          now.getTime() + 30 * 24 * 60 * 60 * 1000
        );

        const upcomingMatches = (data.matches || []).filter((match) => {
          const matchDate = new Date(match.utcDate);
          return (
            (match.status === "SCHEDULED" || match.status === "TIMED") &&
            matchDate >= now &&
            matchDate <= thirtyDaysFromNow
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
        <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 rounded-lg p-8 text-center">
          <div className="text-4xl mb-4">🔑</div>
          <h3 className="text-lg font-semibold mb-2">No Upcoming Matches</h3>
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            To see real match predictions, you need to add a Football API key.
          </p>
          <div className="bg-white dark:bg-slate-900 rounded-lg p-4 text-left max-w-md mx-auto">
            <p className="text-sm font-semibold mb-2">Quick Setup:</p>
            <ol className="text-sm space-y-1 text-slate-600 dark:text-slate-400">
              <li>
                1. Register at{" "}
                <a
                  href="https://www.football-data.org/client/register"
                  target="_blank"
                  className="text-blue-600 hover:underline"
                >
                  football-data.org
                </a>
              </li>
              <li>2. Copy your API key</li>
              <li>
                3. Add to{" "}
                <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded">
                  .env
                </code>
                :{" "}
                <code className="bg-slate-100 dark:bg-slate-800 px-1 rounded">
                  FOOTBALL_API_KEY=your_key
                </code>
              </li>
              <li>4. Restart backend server</li>
            </ol>
          </div>
        </div>
      )}

      {!loading && !error && matches.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {matches.slice(0, 12).map((match) => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      )}
    </div>
  );
}
