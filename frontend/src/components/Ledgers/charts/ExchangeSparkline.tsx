import { Box } from "@chakra-ui/react"
import {
  ColorType,
  createChart,
  type IChartApi,
  LineSeries,
} from "lightweight-charts"
import { useEffect, useRef } from "react"

interface ExchangeSparklineProps {
  data: number[]
  color: string
  height?: number
}

export function ExchangeSparkline({
  data,
  color,
  height = 32,
}: ExchangeSparklineProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  // Re-create chart when data or theme changes

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Convert number[] to { time, value } format required by lightweight-charts
    // Since we don't have timestamps, we use index as time (dummy dates)
    // or just incrementing seconds. Lightweight-charts needs valid time (string or number timestamp).
    // Using unix timestamps
    const now = Math.floor(Date.now() / 1000)
    const chartData = data.map((price, index) => ({
      time: (now - (data.length - index) * 3600) as any, // Hourly intervals backwards from now
      value: price,
    }))

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "transparent",
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      rightPriceScale: {
        visible: false,
      },
      timeScale: {
        visible: false,
      },
      crosshair: {
        vertLine: { visible: false },
        horzLine: { visible: false },
      },
      handleScroll: false,
      handleScale: false,
    })

    const lineSeries = chart.addSeries(LineSeries, {
      color: color,
      lineWidth: 2,
      crosshairMarkerVisible: false,
      priceLineVisible: false,
      lastValueVisible: false,
    })

    lineSeries.setData(chartData)
    chart.timeScale().fitContent()

    chartRef.current = chart

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth })
      }
    }

    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      chart.remove()
    }
  }, [data, color, height])

  return <Box ref={chartContainerRef} width="100%" height={`${height}px`} />
}
