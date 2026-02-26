import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useState,
} from "react"
import { Button } from "../components/ui/button"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "../components/ui/dialog"
import { onError } from "../utils/eventBus"

interface ErrorContextType {
  showError: (message: string) => void
  clearError: () => void
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined)

export const ErrorProvider = ({ children }: { children: ReactNode }) => {
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    return onError((msg) => setError(msg))
  }, [])

  const showError = (message: string) => setError(message)
  const clearError = () => setError(null)

  return (
    <ErrorContext.Provider value={{ showError, clearError }}>
      {children}
      <DialogRoot open={!!error} onOpenChange={(e) => !e.open && clearError()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error Occurred</DialogTitle>
            <DialogCloseTrigger />
          </DialogHeader>
          <DialogBody>{error}</DialogBody>
          <DialogFooter>
            <Button onClick={clearError}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </DialogRoot>
    </ErrorContext.Provider>
  )
}

export const useError = () => {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error("useError must be used within an ErrorProvider")
  }
  return context
}
