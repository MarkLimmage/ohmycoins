import type React from "react"
import { StrategyCard } from "./StrategyCard"

export interface StrategyData {
  id: number | string
  title: string
  sharpe: number
  winRate: number
  drawdown: number
}

interface StrategyMetricsOverviewProps {
  strategies: StrategyData[]
}

export const StrategyMetricsOverview: React.FC<
  StrategyMetricsOverviewProps
> = ({ strategies }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {strategies.map((strategy) => (
        <StrategyCard
          key={strategy.id}
          title={strategy.title}
          sharpe={strategy.sharpe}
          winRate={strategy.winRate}
          drawdown={strategy.drawdown}
        />
      ))}
    </div>
  )
}
