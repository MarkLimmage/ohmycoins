import { Box, Text } from "@chakra-ui/react"
import { Group } from "@visx/group"
import { HeatmapRect } from "@visx/heatmap"
import { ParentSize } from "@visx/responsive"
import { useMemo } from "react"
import type { HumanLedgerData } from "../types"

interface HumanSentimentHeatmapProps {
  data: HumanLedgerData
  onDrillDown?: (id: string) => void
}

const colorBullish = ["#6ee7b7", "#34d399", "#10b981"] // Light to Dark Green
const colorBearish = ["#fca5a5", "#f87171", "#ef4444"] // Light to Dark Red
const colorNeutral = "#e5e7eb"

// Helper to determine color based on sentiment score (-1 to 1)
const getSentimentColor = (score: number) => {
  if (score > 0.7) return colorBullish[2]
  if (score > 0.4) return colorBullish[1]
  if (score > 0) return colorBullish[0]
  if (score === 0) return colorNeutral
  if (score > -0.4) return colorBearish[0]
  if (score > -0.7) return colorBearish[1]
  return colorBearish[2]
}

interface Bin {
  bin: number
  bins: {
    bin: number
    date: string
    sentiment: number
    count?: number
  }[]
}

export function HumanSentimentHeatmap({
  data,
  onDrillDown,
}: HumanSentimentHeatmapProps) {
  // Process data into bins for 5 rows (weeks) x 7 columns (days)
  const heatmapData = useMemo(() => {
    if (!data?.heatmapData) return []

    // Sort by date ascending
    const sortedData = [...data.heatmapData].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    )

    if (sortedData.length === 0) return []

    const weeks: Bin[] = []
    let currentWeek: Bin = { bin: 0, bins: [] }
    let weekIndex = 0

    const firstDate = new Date(sortedData[0].date)
    const startOffset = firstDate.getDay() // 0=Sun

    // Fill initial empty days in first week
    for (let i = 0; i < startOffset; i++) {
      currentWeek.bins.push({ bin: i, date: "", sentiment: 0 })
    }

    sortedData.forEach((day) => {
      const dayOfWeek = new Date(day.date).getDay()

      // If we wrapped around to Sunday (0) and we have data in currentWeek
      if (
        dayOfWeek === 0 &&
        currentWeek.bins.length > 0 &&
        currentWeek.bins.some((b) => b.date !== "")
      ) {
        // Pad remaining
        while (currentWeek.bins.length < 7) {
          currentWeek.bins.push({
            bin: currentWeek.bins.length,
            date: "",
            sentiment: 0,
          })
        }
        weeks.push(currentWeek)
        currentWeek = { bin: ++weekIndex, bins: [] }
      }

      currentWeek.bins.push({
        bin: dayOfWeek,
        date: day.date,
        sentiment: day.sentiment,
      })
    })

    // Push last week
    if (currentWeek.bins.length > 0) {
      while (currentWeek.bins.length < 7) {
        currentWeek.bins.push({
          bin: currentWeek.bins.length,
          date: "",
          sentiment: 0,
        })
      }
      weeks.push(currentWeek)
    }

    return weeks
  }, [data?.heatmapData])

  if (!data?.heatmapData || heatmapData.length === 0) {
    return (
      <Box
        height="200px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        bg="gray.50"
        borderRadius="md"
      >
        <Text color="gray.500">No Sentiment Data Available</Text>
      </Box>
    )
  }

  const xMax = 7 // days
  const yMax = heatmapData.length // weeks

  return (
    <Box
      height="220px"
      width="100%"
      mb={4}
      onClick={() => onDrillDown?.(data.id)}
      cursor={onDrillDown ? "pointer" : "default"}
      role="img"
      aria-label="Sentiment Heatmap"
    >
      <ParentSize>
        {({ width, height }) => {
          const binWidth = width / xMax
          const binHeight = height / yMax
          const radius = 4
          const gap = 2

          return (
            <svg width={width} height={height}>
              <title>Sentiment Heatmap</title>
              <Group>
                {heatmapData.map((week, i) => (
                  <HeatmapRect
                    key={`heatmap-week-${i}`}
                    data={[week]}
                    xScale={(d) => d}
                    yScale={(d) => d}
                    binWidth={binWidth}
                    binHeight={binHeight}
                    gap={gap}
                  >
                    {(heatmap) => {
                      return heatmap.map((heatmapBins) =>
                        heatmapBins.map((bin: any) => {
                          if (!bin.bin?.date) return null
                          return (
                            <rect
                              key={`rect-${bin.row}-${bin.column}`}
                              x={bin.column * binWidth}
                              y={bin.row * binHeight}
                              width={binWidth - gap}
                              height={binHeight - gap}
                              fill={getSentimentColor(bin.bin.sentiment)}
                              rx={radius}
                              ry={radius}
                            >
                              <title>{`${bin.bin.date}: ${bin.bin.sentiment > 0 ? "+" : ""}${bin.bin.sentiment.toFixed(2)}`}</title>
                            </rect>
                          )
                        }),
                      )
                    }}
                  </HeatmapRect>
                ))}
              </Group>
            </svg>
          )
        }}
      </ParentSize>
    </Box>
  )
}
