"use client";

import { MatchProvider } from "@/contexts/MatchContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return <MatchProvider>{children}</MatchProvider>;
}
