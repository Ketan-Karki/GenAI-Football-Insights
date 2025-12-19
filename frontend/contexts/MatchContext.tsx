"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";
import type { Match, Prediction } from "@/lib/api";

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
  const [matches, setMatchesState] = useState<Record<string, Match[]>>(() => {
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem("football_matches_cache");
      return cached ? JSON.parse(cached) : {};
    }
    return {};
  });

  const [predictions, setPredictionsState] = useState<
    Record<number, Prediction>
  >(() => {
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem("football_predictions_cache");
      return cached ? JSON.parse(cached) : {};
    }
    return {};
  });

  const setMatches = useCallback((competition: string, matchList: Match[]) => {
    setMatchesState((prev) => {
      const updated = {
        ...prev,
        [competition]: matchList,
      };
      if (typeof window !== "undefined") {
        localStorage.setItem("football_matches_cache", JSON.stringify(updated));
      }
      return updated;
    });
  }, []);

  const setPrediction = useCallback(
    (matchId: number, prediction: Prediction) => {
      setPredictionsState((prev) => {
        const updated = {
          ...prev,
          [matchId]: prediction,
        };
        if (typeof window !== "undefined") {
          localStorage.setItem(
            "football_predictions_cache",
            JSON.stringify(updated)
          );
        }
        return updated;
      });
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
    if (typeof window !== "undefined") {
      localStorage.removeItem("football_matches_cache");
      localStorage.removeItem("football_predictions_cache");
    }
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
