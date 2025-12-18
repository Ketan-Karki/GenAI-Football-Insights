"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, TrendingUp, Target } from "lucide-react";

interface PredictionHistory {
  id: number;
  matchId: number;
  predictedAt: string;
  teamAName: string;
  teamBName: string;
  predictedTeamAGoals: number;
  predictedTeamBGoals: number;
  predictedOutcome: string;
  predictedWinner: string;
  confidenceScore: number;
  actualTeamAGoals: number | null;
  actualTeamBGoals: number | null;
  actualOutcome: string | null;
  actualWinner: string | null;
  predictionCorrect: boolean | null;
  insights: string[];
  modelVersion: string;
  goalsErrorTeamA: number | null;
  goalsErrorTeamB: number | null;
  matchDate: string;
}

interface AccuracyStats {
  totalPredictions: number;
  correctPredictions: number;
  avgGoalsErrorA: number;
  avgGoalsErrorB: number;
  avgConfidence: number;
  accuracyPercentage: number;
}

export default function PredictionsHistory() {
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [stats, setStats] = useState<AccuracyStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
    fetchStats();
  }, []);

  const fetchPredictions = async () => {
    try {
      const response = await fetch("/api/v1/predictions/history?limit=50");
      const data = await response.json();
      setPredictions(data.predictions || []);
    } catch (error) {
      console.error("Error fetching predictions:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/v1/predictions/accuracy");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading predictions...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Prediction History
          </h1>
          <p className="text-slate-300">
            Track our AI's predictions vs actual results
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-5 h-5 text-blue-400" />
                <p className="text-slate-300 text-sm">Accuracy</p>
              </div>
              <p className="text-3xl font-bold text-white">
                {stats.accuracyPercentage.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-400 mt-1">
                {stats.correctPredictions}/{stats.totalPredictions} correct
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-green-400" />
                <p className="text-slate-300 text-sm">Avg Confidence</p>
              </div>
              <p className="text-3xl font-bold text-white">
                {(stats.avgConfidence * 100).toFixed(0)}%
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
              <p className="text-slate-300 text-sm mb-2">
                Goals Error (Team A)
              </p>
              <p className="text-3xl font-bold text-white">
                ±{stats.avgGoalsErrorA.toFixed(2)}
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20">
              <p className="text-slate-300 text-sm mb-2">
                Goals Error (Team B)
              </p>
              <p className="text-3xl font-bold text-white">
                ±{stats.avgGoalsErrorB.toFixed(2)}
              </p>
            </div>
          </div>
        )}

        {/* Predictions List */}
        <div className="space-y-4">
          {predictions.map((pred) => (
            <div
              key={pred.id}
              className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 hover:border-white/40 transition-all"
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-1">
                    {pred.teamAName} vs {pred.teamBName}
                  </h3>
                  <p className="text-sm text-slate-400">
                    {new Date(pred.matchDate).toLocaleDateString("en-US", {
                      weekday: "short",
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    })}
                  </p>
                </div>

                {pred.predictionCorrect !== null && (
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-full ${
                      pred.predictionCorrect
                        ? "bg-green-500/20 text-green-300 border border-green-500/30"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}
                  >
                    {pred.predictionCorrect ? (
                      <>
                        <CheckCircle2 className="w-5 h-5" />
                        <span className="font-semibold">Correct</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5" />
                        <span className="font-semibold">Incorrect</span>
                      </>
                    )}
                  </div>
                )}
              </div>

              {/* Scores */}
              <div className="grid grid-cols-2 gap-6 mb-4">
                {/* Predicted */}
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-sm font-semibold text-slate-300 mb-2">
                    Predicted
                  </p>
                  <div className="flex items-center justify-center gap-4">
                    <span className="text-3xl font-bold text-white">
                      {pred.predictedTeamAGoals.toFixed(1)}
                    </span>
                    <span className="text-2xl text-slate-400">-</span>
                    <span className="text-3xl font-bold text-white">
                      {pred.predictedTeamBGoals.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-center text-sm text-slate-400 mt-2">
                    {pred.predictedOutcome}
                  </p>
                  <p className="text-center text-xs text-slate-500 mt-1">
                    {(pred.confidenceScore * 100).toFixed(0)}% confidence
                  </p>
                </div>

                {/* Actual */}
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-sm font-semibold text-slate-300 mb-2">
                    Actual
                  </p>
                  {pred.actualTeamAGoals !== null ? (
                    <>
                      <div className="flex items-center justify-center gap-4">
                        <span className="text-3xl font-bold text-white">
                          {pred.actualTeamAGoals}
                        </span>
                        <span className="text-2xl text-slate-400">-</span>
                        <span className="text-3xl font-bold text-white">
                          {pred.actualTeamBGoals}
                        </span>
                      </div>
                      <p className="text-center text-sm text-slate-400 mt-2">
                        {pred.actualOutcome}
                      </p>
                      {pred.goalsErrorTeamA !== null && (
                        <p className="text-center text-xs text-slate-500 mt-1">
                          Error: ±{pred.goalsErrorTeamA.toFixed(1)}, ±
                          {pred.goalsErrorTeamB?.toFixed(1)}
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-center text-slate-500 py-4">
                      Match not finished yet
                    </p>
                  )}
                </div>
              </div>

              {/* Insights */}
              {pred.insights && pred.insights.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-semibold text-slate-300 mb-2">
                    AI Insights:
                  </p>
                  <div className="space-y-1">
                    {pred.insights.map((insight, idx) => (
                      <div
                        key={idx}
                        className="text-sm text-slate-300 bg-white/5 rounded px-3 py-2 flex items-start gap-2"
                      >
                        <span className="text-orange-400 font-bold">•</span>
                        <span>{insight}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Model Version */}
              <div className="mt-4 text-xs text-slate-500">
                Model: {pred.modelVersion} • Predicted:{" "}
                {new Date(pred.predictedAt).toLocaleString()}
              </div>
            </div>
          ))}
        </div>

        {predictions.length === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">
              No prediction history available yet.
            </p>
            <p className="text-slate-500 text-sm mt-2">
              Predictions will appear here after matches are completed.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
