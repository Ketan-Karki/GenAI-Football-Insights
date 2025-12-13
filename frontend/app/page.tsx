import { MatchList } from "@/components/match-list";

export default function Home() {
  return (
    <div className="min-h-screen bg-background dark">
      <header className="bg-[#0B0E11] border-b border-border">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-xl">⚽</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                Football Match Predictions
              </h1>
              <p className="text-xs text-[#848E9C]">
                AI-powered predictions • Premier League
              </p>
            </div>
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
