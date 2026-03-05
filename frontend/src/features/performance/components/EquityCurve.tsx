import type React from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { SafeChart } from "@/components/ui/safe-chart"

interface EquityDataPoint {
  date: string
  equity: number
}

interface EquityCurveProps {
  data: EquityDataPoint[]
}

export const EquityCurve: React.FC<EquityCurveProps> = ({ data }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 h-[400px]">
      <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
        Equity Curve
      </h3>
      {data.length === 0 ? (
        <div className="w-full h-[300px] flex items-center justify-center text-gray-400">
          No equity data available
        </div>
      ) : (
        <div className="w-full h-[300px]">
          <SafeChart>
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e5e7eb"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#9ca3af"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${value}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  color: "#f3f4f6",
                  borderRadius: "0.375rem",
                  border: "none",
                }}
                itemStyle={{ color: "#f3f4f6" }}
              />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#3b82f6"
                strokeWidth={2}
                activeDot={{ r: 8 }}
                dot={false}
              />
            </LineChart>
          </SafeChart>
        </div>
      )}
    </div>
  )
}
