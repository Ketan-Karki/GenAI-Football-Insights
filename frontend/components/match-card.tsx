"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { api, type Match, type Prediction } from "@/lib/api";
import { ShimmerButton } from "./ui/shimmer-button";

interface MatchCardProps {
  match: Match;
}

export function MatchCard({ match }: MatchCardProps) {
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [showBallKnowledge, setShowBallKnowledge] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPrediction() {
      if (match.status !== "SCHEDULED" && match.status !== "TIMED") return;

      try {
        setLoadingPrediction(true);
        setPredictionError(null);
        const pred = await api.getPrediction(match.id);
        setPrediction(pred);
      } catch (err) {
        console.error("Error fetching prediction:", err);
        setPredictionError(
          "AI prediction is temporarily unavailable (rate limiting / data provider error). Try again in a few minutes."
        );
      } finally {
        setLoadingPrediction(false);
      }
    }

    fetchPrediction();
  }, [match.id, match.status]);

  const matchDate = new Date(match.utcDate);
  const isUpcoming = match.status === "SCHEDULED" || match.status === "TIMED";

  const getPredictedWinner = () => {
    if (!prediction) return null;
    // Use predictedWinner from API if available (team-specific)
    if (prediction.predictedWinner) {
      return prediction.predictedWinner;
    }
    // Fallback to generic outcome mapping
    if (prediction.predictedOutcome === "HOME_WIN")
      return match.homeTeam.shortName;
    if (prediction.predictedOutcome === "AWAY_WIN")
      return match.awayTeam.shortName;
    return "Draw";
  };

  return (
    <Card
      className="overflow-hidden border border-border bg-card hover:bg-[#252C35] focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-0 hover-tilt smooth-hover hover:border-primary/30 hover:shadow-lg hover:shadow-primary/10 animate-fade-in-up"
      role="article"
      aria-label={`Match: ${match.homeTeam.name} vs ${match.awayTeam.name}`}
    >
      <div
        className="bg-[#0B0E11] px-4 py-3 flex items-center justify-between border-b border-border"
        role="banner"
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-primary rounded-full" />
          <span className="text-xs font-medium text-[#848E9C] uppercase tracking-wider">
            Matchday {match.matchday}
          </span>
        </div>
        <Badge
          variant="secondary"
          className="bg-[#2B3139] text-[#B7BDC6] border-[#2B3139] text-xs font-medium"
        >
          {matchDate.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          })}
        </Badge>
      </div>

      <CardContent className="p-6 space-y-6">
        <div className="space-y-4">
          <div className="flex items-center gap-3 flex-1 smooth-hover hover:translate-x-1">
            <div className="relative w-12 h-12 shrink-0 smooth-hover hover:scale-110 hover:rotate-3">
              {match.homeTeam.crest ? (
                <Image
                  src={match.homeTeam.crest}
                  alt={match.homeTeam.name}
                  fill
                  className="object-contain"
                  unoptimized
                />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 rounded-full flex items-center justify-center">
                  <span className="text-xl font-bold text-slate-600 dark:text-slate-400">
                    {match.homeTeam.tla}
                  </span>
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-base truncate smooth-hover hover:text-primary">
                {match.homeTeam.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Home</p>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div
              className="text-center px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg"
              role="timer"
              aria-label="Match time"
            >
              <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                {matchDate.toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-1 justify-end smooth-hover hover:-translate-x-1">
            <div className="flex-1 min-w-0 text-right">
              <p className="font-semibold text-base truncate smooth-hover hover:text-primary">
                {match.awayTeam.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Away</p>
            </div>
            <div className="relative w-12 h-12 shrink-0 smooth-hover hover:scale-110 hover:-rotate-3">
              {match.awayTeam.crest ? (
                <Image
                  src={match.awayTeam.crest}
                  alt={`${match.awayTeam.name} crest`}
                  fill
                  className="object-contain"
                />
              ) : (
                <div className="w-12 h-12 bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 rounded-full flex items-center justify-center">
                  <span className="text-xl font-bold text-slate-600 dark:text-slate-400">
                    {match.awayTeam.tla}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {isUpcoming && !loadingPrediction && !prediction && predictionError && (
          <div className="pt-4 border-t-2 border-dashed border-slate-200 dark:border-slate-700 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                AI Prediction
              </span>
              <Badge className="bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-0">
                Unavailable
              </Badge>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900/40 rounded-lg p-3">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {predictionError}
              </p>
            </div>
          </div>
        )}

        {isUpcoming && prediction && !loadingPrediction && (
          <div className="pt-4 border-t-2 border-dashed border-slate-200 dark:border-slate-700 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-[#848E9C] uppercase tracking-wider">
                AI Prediction
              </span>
              <Badge className="bg-success/10 text-success border border-success/20 text-xs font-medium px-2 py-1">
                {(prediction.confidenceScore * 100).toFixed(0)}% Confidence
              </Badge>
            </div>

            <div
              className="bg-[#2B3139] rounded-lg p-4 border border-border"
              role="region"
              aria-label="Prediction result"
            >
              <p
                className="text-center text-xs font-medium text-[#848E9C] mb-2 uppercase tracking-wider"
                aria-label="Prediction label"
              >
                Predicted Winner
              </p>
              <p
                className="text-center text-2xl font-bold text-primary font-numeric"
                aria-live="polite"
              >
                {getPredictedWinner()}
              </p>
            </div>

            <div
              className="grid grid-cols-3 gap-3"
              role="group"
              aria-label="Win probabilities"
            >
              <div className="bg-[#2B3139] rounded-md p-3 text-center border border-border smooth-hover hover:scale-105 hover:border-success hover:shadow-lg hover:shadow-success/20">
                <p className="text-xs text-[#848E9C] mb-1 uppercase tracking-wider">
                  {match.homeTeam.tla}
                </p>
                <p className="text-xl font-black text-success font-numeric">
                  {(prediction.homeWinProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div className="bg-[#2B3139] rounded-md p-3 text-center border border-border smooth-hover hover:scale-105 hover:border-[#B7BDC6] hover:shadow-lg">
                <p className="text-xs text-[#848E9C] mb-1 uppercase tracking-wider">
                  Draw
                </p>
                <p className="text-xl font-black text-[#848E9C] font-numeric">
                  {(prediction.drawProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div className="bg-[#2B3139] rounded-md p-3 text-center border border-border smooth-hover hover:scale-105 hover:border-destructive hover:shadow-lg hover:shadow-destructive/20">
                <p className="text-xs text-[#848E9C] mb-1 uppercase tracking-wider">
                  {match.awayTeam.tla}
                </p>
                <p className="text-xl font-black text-destructive font-numeric">
                  {(prediction.awayWinProbability * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            {prediction.insights && prediction.insights.length > 0 && (
              <div className="mt-3">
                <ShimmerButton
                  onClick={() => setShowBallKnowledge(!showBallKnowledge)}
                  className="w-full font-semibold text-sm shadow-lg"
                  aria-expanded={showBallKnowledge}
                  aria-controls="ball-knowledge-content"
                  background="linear-gradient(90deg, #f97316, #f59e0b)"
                  shimmerDuration="2.5s"
                >
                  <span className="text-lg">⚽</span>
                  <span className="mx-2">
                    {showBallKnowledge ? "Hide" : "Show"} Ball Knowledge
                  </span>
                  <span
                    className={`transition-transform duration-300 ${
                      showBallKnowledge ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </ShimmerButton>

                {showBallKnowledge && (
                  <div
                    id="ball-knowledge-content"
                    className="mt-3 space-y-3 bg-[#2B3139] rounded-lg p-4 border border-border animate-in slide-in-from-top-2 duration-200"
                    role="region"
                    aria-label="Detailed match insights"
                  >
                    <p className="text-xs font-medium text-[#848E9C] uppercase tracking-wider flex items-center gap-2">
                      🧠 Ball Knowledge
                    </p>

                    {prediction.teamStats && (
                      <div
                        className="grid grid-cols-2 gap-3 text-xs text-slate-800 dark:text-slate-100"
                        role="group"
                        aria-label="Team statistics"
                      >
                        <div className="bg-white/80 dark:bg-slate-900/80 rounded-md p-3 border border-slate-200 dark:border-slate-700 hover:border-orange-300 dark:hover:border-orange-700 transition-colors">
                          <p className="font-semibold mb-1">Recent Form</p>
                          <p>
                            {match.homeTeam.shortName}:{" "}
                            {(prediction.teamStats.homeForm * 100).toFixed(0)}%
                            wins
                          </p>
                          <p>
                            {match.awayTeam.shortName}:{" "}
                            {(prediction.teamStats.awayForm * 100).toFixed(0)}%
                            wins
                          </p>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-900/80 rounded-md p-3 border border-slate-200 dark:border-slate-700 hover:border-orange-300 dark:hover:border-orange-700 transition-colors">
                          <p className="font-semibold mb-1">Goals / Game</p>
                          <p>
                            {match.homeTeam.shortName}:{" "}
                            {prediction.teamStats.homeGoalsAvg.toFixed(1)}
                          </p>
                          <p>
                            {match.awayTeam.shortName}:{" "}
                            {prediction.teamStats.awayGoalsAvg.toFixed(1)}
                          </p>
                        </div>
                      </div>
                    )}

                    {prediction.headToHead && (
                      <div className="text-[11px] text-slate-700 dark:text-slate-200 bg-white/50 dark:bg-slate-900/40 rounded-md p-2">
                        <p className="font-semibold mb-1">
                          Head-to-head (recent)
                        </p>
                        <p>
                          {match.homeTeam.shortName}{" "}
                          {prediction.headToHead.homeWins}W · Draws{" "}
                          {prediction.headToHead.draws} ·{" "}
                          {match.awayTeam.shortName}{" "}
                          {prediction.headToHead.awayWins}W
                        </p>
                      </div>
                    )}

                    {prediction.keyPlayers &&
                      (prediction.keyPlayers.home.length > 0 ||
                        prediction.keyPlayers.away.length > 0) && (
                        <div
                          className="text-xs text-slate-800 dark:text-slate-100 bg-white/80 dark:bg-slate-900/80 rounded-md p-3 border border-slate-200 dark:border-slate-700"
                          role="group"
                          aria-label="Key players"
                        >
                          <p className="font-semibold mb-2">Key players</p>

                          {prediction.keyPlayers.home.length > 0 && (
                            <div className="mb-2">
                              <p className="font-medium text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                                {match.homeTeam.shortName}
                              </p>
                              {prediction.keyPlayers.home.map((player, idx) => (
                                <p key={idx} className="ml-2">
                                  {player.name} ({player.position?.charAt(0)}) –{" "}
                                  {player.goals} G, {player.assists} A
                                </p>
                              ))}
                            </div>
                          )}

                          {prediction.keyPlayers.away.length > 0 && (
                            <div>
                              <p className="font-medium text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                                {match.awayTeam.shortName}
                              </p>
                              {prediction.keyPlayers.away.map((player, idx) => (
                                <p key={idx} className="ml-2">
                                  {player.name} ({player.position?.charAt(0)}) –{" "}
                                  {player.goals} G, {player.assists} A
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                    {prediction.insights && prediction.insights.length > 0 && (
                      <div className="space-y-2">
                        {prediction.insights.map((insight, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-xs text-slate-800 dark:text-slate-200 bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30 rounded-md p-3 border border-orange-100 dark:border-orange-900/50 hover:border-orange-300 dark:hover:border-orange-700 transition-colors"
                            role="listitem"
                          >
                            <span
                              className="text-orange-600 dark:text-orange-400 font-bold text-sm"
                              aria-hidden="true"
                            >
                              •
                            </span>
                            <span>{insight}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {prediction.modelVersion && (
                      <p
                        className="text-xs text-slate-600 dark:text-slate-400 italic mt-2 pt-3 border-t border-orange-200 dark:border-orange-800"
                        role="contentinfo"
                      >
                        Engine: {prediction.modelVersion}
                        {prediction.modelAccuracy && (
                          <span className="ml-2">
                            • Accuracy:{" "}
                            {(prediction.modelAccuracy * 100).toFixed(1)}%
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {isUpcoming && loadingPrediction && (
          <div className="pt-4 border-t-2 border-dashed border-slate-200 dark:border-slate-700">
            <div className="space-y-2">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
              <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
