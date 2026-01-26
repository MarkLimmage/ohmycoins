import { createFileRoute } from "@tanstack/react-router"
import { StrategyMetricsOverview } from "@/features/performance/components/StrategyMetricsOverview"
import { PerformanceVisuals } from "@/features/performance/components/PerformanceVisuals"

export const Route = createFileRoute("/_layout/performance")({
  component: PerformanceDashboard,
})

const mockStrategies = [
  { id: 1, title: "Momentum Alpha", sharpe: 2.4, winRate: 0.65, drawdown: 0.12 },
  { id: 2, title: "Mean Reversion", sharpe: 1.8, winRate: 0.55, drawdown: 0.08 },
  { id: 3, title: "Trend Follower", sharpe: 0.9, winRate: 0.40, drawdown: 0.25 },
]

const mockEquityData = [
  { date: "2024-01-01", equity: 10000 },
  { date: "2024-02-01", equity: 10500 },
  { date: "2024-03-01", equity: 10200 },
  { date: "2024-04-01", equity: 11000 },
  { date: "2024-05-01", equity: 11500 },
  { date: "2024-06-01", equity: 11300 },
  { date: "2024-07-01", equity: 12100 },
]

function PerformanceDashboard() {
  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8 overflow-y-auto">
      <header className="mb-4">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Performance Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">Monitor your strategies and equity growth.</p>
      </header>

      <section>
        <StrategyMetricsOverview strategies={mockStrategies} />
      </section>

      <section>
        <PerformanceVisuals equityData={mockEquityData} />
      </section>
    </div>
  )
}
