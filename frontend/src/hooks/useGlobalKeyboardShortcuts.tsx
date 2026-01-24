/**
 * Global keyboard shortcuts handler for Oh My Coins
 *
 * Implements REQ-UX-004: Global keyboard shortcuts
 * - Ctrl+Shift+K: Focus Kill Switch (when active)
 * - Ctrl+Shift+T: Toggle all table views
 */

import { useCallback, useEffect } from "react"

export interface KeyboardShortcutHandlers {
  onToggleTableViews?: () => void
  onFocusKillSwitch?: () => void
}

/**
 * Hook to handle global keyboard shortcuts
 *
 * @param handlers - Object containing callback functions for each shortcut
 *
 * @example
 * ```tsx
 * function App() {
 *   const [showTableViews, setShowTableViews] = useState(false);
 *
 *   useGlobalKeyboardShortcuts({
 *     onToggleTableViews: () => setShowTableViews(prev => !prev),
 *     onFocusKillSwitch: () => {
 *       const killSwitch = document.getElementById('kill-switch');
 *       killSwitch?.focus();
 *     }
 *   });
 *
 *   return <YourApp />;
 * }
 * ```
 */
export function useGlobalKeyboardShortcuts(handlers: KeyboardShortcutHandlers) {
  const { onToggleTableViews, onFocusKillSwitch } = handlers

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Check for Ctrl+Shift+T (toggle table views)
      if (
        (event.ctrlKey || event.metaKey) &&
        event.shiftKey &&
        event.key === "T"
      ) {
        event.preventDefault()
        onToggleTableViews?.()
        return
      }

      // Check for Ctrl+Shift+K (focus kill switch)
      if (
        (event.ctrlKey || event.metaKey) &&
        event.shiftKey &&
        event.key === "K"
      ) {
        event.preventDefault()
        onFocusKillSwitch?.()
        return
      }
    },
    [onToggleTableViews, onFocusKillSwitch],
  )

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown)
    return () => {
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [handleKeyDown])
}

/**
 * Context for managing global table view state
 */
import { createContext, type ReactNode, useContext, useState } from "react"

interface TableViewContextType {
  showTableViews: boolean
  toggleTableViews: () => void
  setShowTableViews: (show: boolean) => void
}

const TableViewContext = createContext<TableViewContextType | undefined>(
  undefined,
)

/**
 * Provider for global table view state
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <TableViewProvider>
 *       <YourApp />
 *     </TableViewProvider>
 *   );
 * }
 * ```
 */
export function TableViewProvider({ children }: { children: ReactNode }) {
  const [showTableViews, setShowTableViews] = useState(false)

  const toggleTableViews = useCallback(() => {
    setShowTableViews((prev) => !prev)
  }, [])

  // Set up global keyboard shortcuts
  useGlobalKeyboardShortcuts({
    onToggleTableViews: toggleTableViews,
    onFocusKillSwitch: () => {
      const killSwitch = document.getElementById("kill-switch-button")
      if (killSwitch) {
        killSwitch.focus()
        // Scroll into view if needed
        killSwitch.scrollIntoView({ behavior: "smooth", block: "center" })
      }
    },
  })

  return (
    <TableViewContext.Provider
      value={{ showTableViews, toggleTableViews, setShowTableViews }}
    >
      {children}
    </TableViewContext.Provider>
  )
}

/**
 * Hook to access global table view state
 *
 * @example
 * ```tsx
 * function LedgerCard() {
 *   const { showTableViews, toggleTableViews } = useTableView();
 *
 *   return (
 *     <div>
 *       {showTableViews ? <TableView /> : <ChartView />}
 *       <button onClick={toggleTableViews}>Toggle View</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTableView() {
  const context = useContext(TableViewContext)
  if (context === undefined) {
    throw new Error("useTableView must be used within a TableViewProvider")
  }
  return context
}

/**
 * Component that shows keyboard shortcut hints
 */
import { Box, HStack, Kbd, Text } from "@chakra-ui/react"

export function KeyboardShortcutHints() {
  return (
    <Box
      position="fixed"
      bottom={4}
      left={4}
      bg="gray.800"
      color="white"
      p={3}
      borderRadius="md"
      fontSize="sm"
      opacity={0.8}
      zIndex={1000}
      aria-label="Keyboard shortcuts"
    >
      <Text fontWeight="bold" mb={2}>
        Keyboard Shortcuts
      </Text>
      <HStack gap={4} flexWrap="wrap">
        <HStack>
          <Kbd>Ctrl</Kbd>
          <Text>+</Text>
          <Kbd>Shift</Kbd>
          <Text>+</Text>
          <Kbd>T</Kbd>
          <Text>Toggle Tables</Text>
        </HStack>
        <HStack>
          <Kbd>Ctrl</Kbd>
          <Text>+</Text>
          <Kbd>Shift</Kbd>
          <Text>+</Text>
          <Kbd>K</Kbd>
          <Text>Focus Kill Switch</Text>
        </HStack>
      </HStack>
      <Text fontSize="xs" color="gray.400" mt={2}>
        Press Esc to close modals
      </Text>
    </Box>
  )
}
