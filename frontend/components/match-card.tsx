"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { api, type Match, type Prediction } from "@/lib/api";

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
    <Card className="overflow-hidden hover:shadow-xl transition-all duration-300 border-2 hover:border-green-500/50 bg-linear-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-800">
      <div className="bg-linear-to-r from-green-600 to-emerald-600 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
          <span className="text-xs font-semibold text-white uppercase tracking-wide">
            Matchday {match.matchday}
          </span>
        </div>
        <Badge
          variant="secondary"
          className="bg-white/20 text-white border-white/30"
        >
          {matchDate.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          })}
        </Badge>
      </div>

      <CardContent className="p-6 space-y-6">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            {match.homeTeam.crest ? (
              <div className="relative w-12 h-12 shrink-0">
                <Image
                  src={match.homeTeam.crest}
                  alt={match.homeTeam.name}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            ) : (
              <div className="w-12 h-12 shrink-0 bg-linear-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 rounded-full flex items-center justify-center">
                <span className="text-xl font-bold text-slate-600 dark:text-slate-400">
                  {match.homeTeam.tla}
                </span>
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-bold text-lg truncate text-slate-900 dark:text-slate-100">
                {match.homeTeam.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Home</p>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div className="text-center px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
              <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                {matchDate.toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {match.awayTeam.crest ? (
              <div className="relative w-12 h-12 shrink-0">
                <Image
                  src={match.awayTeam.crest}
                  alt={match.awayTeam.name}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            ) : (
              <div className="w-12 h-12 shrink-0 bg-linear-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 rounded-full flex items-center justify-center">
                <span className="text-xl font-bold text-slate-600 dark:text-slate-400">
                  {match.awayTeam.tla}
                </span>
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="font-bold text-lg truncate text-slate-900 dark:text-slate-100">
                {match.awayTeam.name}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Away</p>
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
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wide">
                AI Prediction
              </span>
              <Badge className="bg-linear-to-r from-purple-600 to-pink-600 text-white border-0">
                {(prediction.confidenceScore * 100).toFixed(0)}% Confidence
              </Badge>
            </div>

            <div className="bg-linear-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 rounded-lg p-4 border-2 border-green-200 dark:border-green-800">
              <p className="text-center text-sm font-bold text-green-700 dark:text-green-400 mb-2">
                Predicted Winner
              </p>
              <p className="text-center text-2xl font-black bg-linear-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                {getPredictedWinner()}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1 truncate">
                  {match.homeTeam.tla}
                </p>
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {(prediction.homeWinProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div className="text-center p-2 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">
                  Draw
                </p>
                <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                  {(prediction.drawProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div className="text-center p-2 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1 truncate">
                  {match.awayTeam.tla}
                </p>
                <p className="text-lg font-bold text-red-600 dark:text-red-400">
                  {(prediction.awayWinProbability * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {prediction.ballKnowledge &&
              prediction.ballKnowledge.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => setShowBallKnowledge(!showBallKnowledge)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-linear-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white rounded-lg font-semibold text-sm transition-all shadow-md hover:shadow-lg"
                  >
                    <span className="text-lg">⚽</span>
                    <span>
                      {showBallKnowledge ? "Hide" : "Show"} Ball Knowledge
                    </span>
                    <span
                      className={`transition-transform ${
                        showBallKnowledge ? "rotate-180" : ""
                      }`}
                    >
                      ▼
                    </span>
                  </button>

                  {showBallKnowledge && (
                    <div className="mt-3 space-y-3 bg-linear-to-br from-orange-50 to-amber-50 dark:from-orange-950/20 dark:to-amber-950/20 rounded-lg p-4 border-2 border-orange-200 dark:border-orange-800">
                      <p className="text-xs font-bold text-orange-700 dark:text-orange-400 uppercase tracking-wide">
                        🧠 Ball Knowledge
                      </p>

                      {prediction.teamStats && (
                        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-700 dark:text-slate-200">
                          <div className="bg-white/60 dark:bg-slate-900/60 rounded-md p-2">
                            <p className="font-semibold mb-1">Recent Form</p>
                            <p>
                              {match.homeTeam.shortName}:{" "}
                              {(prediction.teamStats.homeForm * 100).toFixed(0)}
                              % wins
                            </p>
                            <p>
                              {match.awayTeam.shortName}:{" "}
                              {(prediction.teamStats.awayForm * 100).toFixed(0)}
                              % wins
                            </p>
                          </div>
                          <div className="bg-white/60 dark:bg-slate-900/60 rounded-md p-2">
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
                          <div className="text-[11px] text-slate-700 dark:text-slate-200 bg-white/50 dark:bg-slate-900/40 rounded-md p-2">
                            <p className="font-semibold mb-2">Key players</p>

                            {prediction.keyPlayers.home.length > 0 && (
                              <div className="mb-2">
                                <p className="font-medium text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                                  {match.homeTeam.shortName}
                                </p>
                                {prediction.keyPlayers.home.map(
                                  (player, idx) => (
                                    <p key={idx} className="ml-2">
                                      {player.name} (
                                      {player.position?.charAt(0)}) –{" "}
                                      {player.goals} G, {player.assists} A
                                    </p>
                                  )
                                )}
                              </div>
                            )}

                            {prediction.keyPlayers.away.length > 0 && (
                              <div>
                                <p className="font-medium text-[10px] text-slate-500 dark:text-slate-400 mb-1">
                                  {match.awayTeam.shortName}
                                </p>
                                {prediction.keyPlayers.away.map(
                                  (player, idx) => (
                                    <p key={idx} className="ml-2">
                                      {player.name} (
                                      {player.position?.charAt(0)}) –{" "}
                                      {player.goals} G, {player.assists} A
                                    </p>
                                  )
                                )}
                              </div>
                            )}
                          </div>
                        )}

                      {prediction.insights &&
                        prediction.insights.length > 0 && (
                          <div className="space-y-2">
                            <p className="text-[10px] font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-wide">
                              🤖 ML Insights
                            </p>
                            {prediction.insights.map((insight, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 bg-linear-to-r from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30 rounded p-2"
                              >
                                <span className="text-orange-500 font-bold">
                                  •
                                </span>
                                <span>{insight}</span>
                              </div>
                            ))}
                          </div>
                        )}

                      {prediction.ballKnowledge &&
                        prediction.ballKnowledge.map((insight, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 bg-white/50 dark:bg-slate-900/50 rounded p-2"
                          >
                            <span className="text-orange-500 font-bold">•</span>
                            <span>{insight}</span>
                          </div>
                        ))}

                      {prediction.modelVersion && (
                        <p className="text-[10px] text-slate-500 dark:text-slate-400 italic mt-1 pt-2 border-t border-orange-200 dark:border-orange-800">
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
