import { cloneElement, useEffect, useRef, useState } from "react"

interface SafeChartProps {
  children: React.ReactElement<{ width?: number; height?: number }>
}

/**
 * Drop-in replacement for Recharts ResponsiveContainer that measures
 * the parent via ResizeObserver and passes pixel dimensions directly
 * to the chart child, bypassing ResponsiveContainer entirely.
 */
export const SafeChart = ({ children }: SafeChartProps) => {
  const ref = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState<{ width: number; height: number } | null>(
    null,
  )

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        if (width > 0 && height > 0) {
          setSize({ width, height })
        }
      }
    })

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} style={{ width: "100%", height: "100%" }}>
      {size && cloneElement(children, { width: size.width, height: size.height })}
    </div>
  )
}
