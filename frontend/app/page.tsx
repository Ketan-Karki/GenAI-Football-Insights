import { MatchList } from "@/components/match-list";
import { GlitchText } from "@/components/glitch-text";
import { Target } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-background dark">
      <header className="bg-[#0B0E11] border-b border-border sticky top-0 z-50 backdrop-blur-sm bg-opacity-95">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center smooth-hover hover:scale-110 hover:rotate-12 animate-pulse-glow">
                <span className="text-xl">⚽</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">
                  <GlitchText text="Football Match Predictions" />
                </h1>
                <p className="text-xs text-[#848E9C] smooth-hover hover:text-[#B7BDC6]">
                  AI-powered predictions • Real-time insights
                </p>
              </div>
            </div>
            <a
              href="/predictions-history"
              className="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-lg rounded-lg border border-white/20 text-white font-medium transition-all duration-200 flex items-center gap-2"
            >
              <Target className="w-4 h-4" />
              Prediction History
            </a>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-6">
        <MatchList />
      </main>

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
