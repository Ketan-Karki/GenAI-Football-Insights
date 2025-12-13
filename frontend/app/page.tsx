import { MatchList } from "@/components/match-list";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-green-50/30 to-slate-100 dark:from-slate-950 dark:via-green-950/10 dark:to-slate-900">
      <div className="absolute inset-0 bg-[url('/pitch-pattern.svg')] opacity-5 pointer-events-none" />

      <header className="relative border-b bg-white/80 backdrop-blur-md dark:bg-slate-950/80 shadow-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-green-600 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
                <span className="text-2xl">⚽</span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 bg-clip-text text-transparent">
                Football Predictions
              </h1>
            </div>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl">
              AI-powered match predictions using advanced machine learning • Get
              insights before kickoff
            </p>
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-500">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Live Predictions</span>
              </div>
              <span>•</span>
              <span>Updated Daily</span>
              <span>•</span>
              <span>5 Major Leagues</span>
            </div>
          </div>
        </div>
      </header>

      <main className="relative container mx-auto px-4 py-12">
        <MatchList />
      </main>

      <footer className="relative border-t bg-white/50 dark:bg-slate-950/50 backdrop-blur-sm mt-16 py-8">
        <div className="container mx-auto px-4 text-center space-y-2">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Powered by <span className="font-semibold">football-data.org</span>{" "}
            API
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-500">
            Built with Next.js, Go, Python ML & PostgreSQL
          </p>
        </div>
      </footer>
    </div>
  );
}
