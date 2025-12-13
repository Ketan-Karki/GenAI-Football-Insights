"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { api, type Match, type Prediction } from "@/lib/api";
import { Sparkles } from "./ui/sparkles";
import { BackgroundGradient } from "./ui/background-gradient";

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
      className="overflow-hidden hover:shadow-xl transition-all duration-300 border-2 hover:border-green-500/50 bg-gradient-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-800 focus-within:ring-2 focus-within:ring-green-500 focus-within:ring-offset-2"
      role="article"
      aria-label={`Match: ${match.homeTeam.name} vs ${match.awayTeam.name}`}
    >
      <div
        className="bg-gradient-to-r from-green-600 to-emerald-600 px-4 py-2 flex items-center justify-between"
        role="banner"
      >
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
              <BackgroundGradient
                className="rounded-full"
                containerClassName="inline-block"
              >
                <Badge className="bg-gradient-to-r from-purple-600 to-pink-600 text-white border-0">
                  {(prediction.confidenceScore * 100).toFixed(0)}% Confidence
                </Badge>
              </BackgroundGradient>
            </div>

            <div
              className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 rounded-lg p-4 border-2 border-green-200 dark:border-green-800 shadow-sm"
              role="region"
              aria-label="Prediction result"
            >
              <p
                className="text-center text-sm font-bold text-green-800 dark:text-green-300 mb-2"
                aria-label="Prediction label"
              >
                Predicted Winner
              </p>
              <div className="relative">
                <Sparkles
                  particleColor="#10b981"
                  particleDensity={30}
                  minSize={0.6}
                  maxSize={1.4}
                  className="absolute inset-0"
                />
                <p
                  className="relative z-10 text-center text-2xl font-black text-green-700 dark:text-green-300"
                  aria-live="polite"
                >
                  {getPredictedWinner()}
                </p>
              </div>
            </div>

            <div
              className="grid grid-cols-3 gap-3"
              role="group"
              aria-label="Win probabilities"
            >
              <div
                className="text-center p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 border-2 border-blue-300 dark:border-blue-700 hover:border-blue-500 dark:hover:border-blue-500 transition-all hover:shadow-md transform hover:-translate-y-0.5"
                role="status"
                aria-label={`${match.homeTeam.tla} win probability`}
              >
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 truncate uppercase tracking-wide">
                  {match.homeTeam.tla}
                </p>
                <p className="text-xl font-black text-blue-700 dark:text-blue-300">
                  {(prediction.homeWinProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div
                className="text-center p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border-2 border-yellow-300 dark:border-yellow-700 hover:border-yellow-500 dark:hover:border-yellow-500 transition-all hover:shadow-md transform hover:-translate-y-0.5"
                role="status"
                aria-label="Draw probability"
              >
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 uppercase tracking-wide">
                  Draw
                </p>
                <p className="text-xl font-black text-yellow-700 dark:text-yellow-300">
                  {(prediction.drawProbability * 100).toFixed(0)}%
                </p>
              </div>
              <div
                className="text-center p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border-2 border-red-300 dark:border-red-700 hover:border-red-500 dark:hover:border-red-500 transition-all hover:shadow-md transform hover:-translate-y-0.5"
                role="status"
                aria-label={`${match.awayTeam.tla} win probability`}
              >
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1 truncate uppercase tracking-wide">
                  {match.awayTeam.tla}
                </p>
                <p className="text-xl font-black text-red-700 dark:text-red-300">
                  {(prediction.awayWinProbability * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {prediction.ballKnowledge &&
              prediction.ballKnowledge.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => setShowBallKnowledge(!showBallKnowledge)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white rounded-lg font-semibold text-sm transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
                    aria-expanded={showBallKnowledge}
                    aria-controls="ball-knowledge-content"
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
                    <div
                      id="ball-knowledge-content"
                      className="mt-3 space-y-3 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/20 dark:to-amber-950/20 rounded-lg p-4 border-2 border-orange-200 dark:border-orange-800 animate-in slide-in-from-top-2 duration-300"
                      role="region"
                      aria-label="Detailed match insights"
                    >
                      <p className="text-xs font-bold text-orange-800 dark:text-orange-300 uppercase tracking-wide flex items-center gap-2">
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
                              {(prediction.teamStats.homeForm * 100).toFixed(0)}
                              % wins
                            </p>
                            <p>
                              {match.awayTeam.shortName}:{" "}
                              {(prediction.teamStats.awayForm * 100).toFixed(0)}
                              % wins
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
                            <p className="text-xs font-bold text-orange-800 dark:text-orange-300 uppercase tracking-wide flex items-center gap-1">
                              🤖 ML Insights
                            </p>
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

                      {prediction.ballKnowledge &&
                        prediction.ballKnowledge.map((insight, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-xs text-slate-800 dark:text-slate-200 bg-white/80 dark:bg-slate-900/80 rounded-md p-3 border border-slate-200 dark:border-slate-700 hover:border-orange-300 dark:hover:border-orange-700 transition-colors"
                            role="listitem"
                          >
                            <span
                              className="text-orange-600 dark:text-orange-400 font-bold"
                              aria-hidden="true"
                            >
                              •
                            </span>
                            <span>{insight}</span>
                          </div>
                        ))}

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
