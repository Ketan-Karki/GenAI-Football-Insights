"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";
import type { Match } from "@/lib/api";

interface Prediction {
  matchId: number;
  homeWinProbability: number;
  drawProbability: number;
  awayWinProbability: number;
  predictedWinner: string;
  predictedOutcome: string;
  insights?: string[];
  confidenceScore?: number;
  modelVersion?: string;
  modelAccuracy?: number;
}

interface MatchContextType {
  matches: Record<string, Match[]>;
  predictions: Record<number, Prediction>;
  setMatches: (competition: string, matches: Match[]) => void;
  setPrediction: (matchId: number, prediction: Prediction) => void;
  getMatches: (competition: string) => Match[] | undefined;
  getPrediction: (matchId: number) => Prediction | undefined;
  clearCache: () => void;
}

const MatchContext = createContext<MatchContextType | undefined>(undefined);

export function MatchProvider({ children }: { children: ReactNode }) {
  const [matches, setMatchesState] = useState<Record<string, Match[]>>({});
  const [predictions, setPredictionsState] = useState<
    Record<number, Prediction>
  >({});

  const setMatches = useCallback((competition: string, matchList: Match[]) => {
    setMatchesState((prev) => ({
      ...prev,
      [competition]: matchList,
    }));
  }, []);

  const setPrediction = useCallback(
    (matchId: number, prediction: Prediction) => {
      setPredictionsState((prev) => ({
        ...prev,
        [matchId]: prediction,
      }));
    },
    []
  );

  const getMatches = useCallback(
    (competition: string) => {
      return matches[competition];
    },
    [matches]
  );

  const getPrediction = useCallback(
    (matchId: number) => {
      return predictions[matchId];
    },
    [predictions]
  );

  const clearCache = useCallback(() => {
    setMatchesState({});
    setPredictionsState({});
  }, []);

  return (
    <MatchContext.Provider
      value={{
        matches,
        predictions,
        setMatches,
        setPrediction,
        getMatches,
        getPrediction,
        clearCache,
      }}
    >
      {children}
    </MatchContext.Provider>
  );
}

export function useMatchContext() {
  const context = useContext(MatchContext);
  if (!context) {
    throw new Error("useMatchContext must be used within a MatchProvider");
  }
  return context;
}
