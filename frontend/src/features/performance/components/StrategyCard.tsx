import React from "react"

interface StrategyCardProps {
  title: string
  sharpe: number
  winRate: number
  drawdown: number // Percentage
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  title,
  sharpe,
  winRate,
  drawdown,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">{title}</h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">Sharpe</span>
          <span className={`text-xl font-semibold ${sharpe >= 1 ? 'text-green-600' : 'text-yellow-600'}`}>
            {sharpe.toFixed(2)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">Win Rate</span>
          <span className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {(winRate * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">Drawdown</span>
          <span className="text-xl font-semibold text-red-600">
            {(drawdown * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}
