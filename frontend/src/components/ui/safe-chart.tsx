import { useEffect, useRef, useState } from "react"
import { ResponsiveContainer } from "recharts"

type Dimension = number | `${number}%`

interface SafeChartProps {
  children: React.ReactElement
  width?: Dimension
  height?: Dimension
}

/**
 * Wrapper around Recharts ResponsiveContainer that waits for the parent
 * to have positive dimensions before rendering. This prevents the
 * "width(-1) and height(-1)" console warning that fires when charts
 * render before their container has been laid out by the browser.
 */
export const SafeChart = ({
  children,
  width = "100%",
  height = "100%",
}: SafeChartProps) => {
  const ref = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          setReady(true)
          observer.disconnect()
        }
      }
    })

    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} style={{ width: "100%", height: "100%" }}>
      {ready && (
        <ResponsiveContainer width={width} height={height}>
          {children}
        </ResponsiveContainer>
      )}
    </div>
  )
}
