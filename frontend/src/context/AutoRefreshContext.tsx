import { createContext, type ReactNode, useContext, useState } from "react"

interface AutoRefreshContextType {
  isEnabled: boolean
  toggle: () => void
  interval: number
  setInterval: (interval: number) => void
}

const AutoRefreshContext = createContext<AutoRefreshContextType | undefined>(
  undefined,
)

export const AutoRefreshProvider = ({ children }: { children: ReactNode }) => {
  const [isEnabled, setIsEnabled] = useState(true)
  const [interval, setIntervalState] = useState(30000) // Default 30s

  const toggle = () => setIsEnabled((prev) => !prev)
  const setInterval = (newInterval: number) => setIntervalState(newInterval)

  return (
    <AutoRefreshContext.Provider
      value={{ isEnabled, toggle, interval, setInterval }}
    >
      {children}
    </AutoRefreshContext.Provider>
  )
}

export const useAutoRefresh = () => {
  const context = useContext(AutoRefreshContext)
  if (!context) {
    throw new Error("useAutoRefresh must be used within an AutoRefreshProvider")
  }
  return context
}
