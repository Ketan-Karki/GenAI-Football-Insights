"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  XCircle,
  TrendingUp,
  Target,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";

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
      <div className="min-h-screen bg-background dark flex items-center justify-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background dark">
      {/* Header */}
      <header className="bg-[#0B0E11] border-b border-border sticky top-0 z-50 backdrop-blur-sm bg-opacity-95">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 text-white font-medium transition-all duration-200"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Matches
            </Link>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                Prediction History
              </h1>
              <p className="text-xs text-[#848E9C]">
                Track our AI's predictions vs actual results
              </p>
            </div>
            <div className="w-32" />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-[#2B3139] border border-border rounded-lg p-6 hover:border-primary/30 smooth-hover">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-5 h-5 text-primary" />
                <p className="text-[#848E9C] text-sm">Accuracy</p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {stats.accuracyPercentage.toFixed(1)}%
              </p>
              <p className="text-xs text-[#848E9C] mt-1">
                {stats.correctPredictions}/{stats.totalPredictions} correct
              </p>
            </div>

            <div className="bg-[#2B3139] border border-border rounded-lg p-6 hover:border-primary/30 smooth-hover">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                <p className="text-[#848E9C] text-sm">Avg Confidence</p>
              </div>
              <p className="text-3xl font-bold text-foreground">
                {(stats.avgConfidence * 100).toFixed(0)}%
              </p>
            </div>

            <div className="bg-[#2B3139] border border-border rounded-lg p-6 hover:border-primary/30 smooth-hover">
              <p className="text-[#848E9C] text-sm mb-2">
                Goals Error (Team A)
              </p>
              <p className="text-3xl font-bold text-foreground">
                ±{stats.avgGoalsErrorA.toFixed(2)}
              </p>
            </div>

            <div className="bg-[#2B3139] border border-border rounded-lg p-6 hover:border-primary/30 smooth-hover">
              <p className="text-[#848E9C] text-sm mb-2">
                Goals Error (Team B)
              </p>
              <p className="text-3xl font-bold text-foreground">
                ±{stats.avgGoalsErrorB.toFixed(2)}
              </p>
            </div>
          </div>
        )}

        {/* Predictions List */}
        {predictions.length > 0 ? (
          <div className="space-y-4">
            {predictions.map((pred) => (
              <div
                key={pred.id}
                className="bg-[#2B3139] border border-border rounded-lg p-6 hover:border-primary/30 smooth-hover transition-all"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-foreground mb-1">
                      {pred.teamAName} vs {pred.teamBName}
                    </h3>
                    <p className="text-sm text-[#848E9C]">
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
                          <span className="font-semibold text-sm">Correct</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-5 h-5" />
                          <span className="font-semibold text-sm">
                            Incorrect
                          </span>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Scores */}
                <div className="grid grid-cols-2 gap-6 mb-4">
                  {/* Predicted */}
                  <div className="bg-[#0B0E11] rounded-lg p-4">
                    <p className="text-sm font-semibold text-[#848E9C] mb-2">
                      Predicted
                    </p>
                    <div className="flex items-center justify-center gap-4">
                      <span className="text-3xl font-bold text-foreground">
                        {pred.predictedTeamAGoals.toFixed(1)}
                      </span>
                      <span className="text-2xl text-[#848E9C]">-</span>
                      <span className="text-3xl font-bold text-foreground">
                        {pred.predictedTeamBGoals.toFixed(1)}
                      </span>
                    </div>
                    <p className="text-center text-sm text-[#848E9C] mt-2">
                      {pred.predictedOutcome}
                    </p>
                    <p className="text-center text-xs text-[#6B7280] mt-1">
                      {(pred.confidenceScore * 100).toFixed(0)}% confidence
                    </p>
                  </div>

                  {/* Actual */}
                  <div className="bg-[#0B0E11] rounded-lg p-4">
                    <p className="text-sm font-semibold text-[#848E9C] mb-2">
                      Actual
                    </p>
                    {pred.actualTeamAGoals !== null ? (
                      <>
                        <div className="flex items-center justify-center gap-4">
                          <span className="text-3xl font-bold text-foreground">
                            {pred.actualTeamAGoals}
                          </span>
                          <span className="text-2xl text-[#848E9C]">-</span>
                          <span className="text-3xl font-bold text-foreground">
                            {pred.actualTeamBGoals}
                          </span>
                        </div>
                        <p className="text-center text-sm text-[#848E9C] mt-2">
                          {pred.actualOutcome}
                        </p>
                        {pred.goalsErrorTeamA !== null && (
                          <p className="text-center text-xs text-[#6B7280] mt-1">
                            Error: ±{pred.goalsErrorTeamA.toFixed(1)}, ±
                            {pred.goalsErrorTeamB?.toFixed(1)}
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="text-center text-[#6B7280] py-4">
                        Match not finished yet
                      </p>
                    )}
                  </div>
                </div>

                {/* Insights */}
                {pred.insights && pred.insights.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-semibold text-[#848E9C] mb-2">
                      AI Insights:
                    </p>
                    <div className="space-y-1">
                      {pred.insights.map((insight, idx) => (
                        <div
                          key={idx}
                          className="text-sm text-[#B7BDC6] bg-[#0B0E11] rounded px-3 py-2 flex items-start gap-2"
                        >
                          <span className="text-primary font-bold">•</span>
                          <span>{insight}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Model Version */}
                <div className="mt-4 text-xs text-[#6B7280]">
                  Model: {pred.modelVersion} • Predicted:{" "}
                  {new Date(pred.predictedAt).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[#2B3139] border border-border rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-bold text-foreground mb-2">
              No Prediction History
            </h3>
            <p className="text-[#848E9C] text-sm">
              Predictions will appear here after matches are completed.
            </p>
            <p className="text-[#6B7280] text-sm mt-2">
              Data is populated when matches finish and results are recorded.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-[#0B0E11] border-t border-border mt-12">
        <div className="container mx-auto px-6 py-4 text-center">
          <p className="text-xs text-[#848E9C]">
            Powered by AI & Football Data
          </p>
        </div>
      </footer>
    </div>
  );
}
