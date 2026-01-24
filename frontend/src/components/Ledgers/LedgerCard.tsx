import { Box, Button, Card, Flex, Skeleton, Text } from "@chakra-ui/react"
import { formatDistanceToNow } from "date-fns"
import {
  type ComponentState,
  LEDGER_CONFIG,
  type LedgerCardProps,
} from "./types"
import "./ledger-styles.css"

/**
 * Base LedgerCard component
 * Handles 4 states: loading, error, empty, live
 * REQ-UX-001, REQ-UX-004, REQ-UX-005
 */
export function LedgerCard({
  ledgerType,
  data,
  alertLevel = "normal",
  isLoading = false,
  error = null,
  showTableView = false,
  onToggleTableView,
  children,
}: LedgerCardProps & { children?: React.ReactNode }) {
  const config = LEDGER_CONFIG[ledgerType]
  const state: ComponentState = isLoading
    ? "loading"
    : error
      ? "error"
      : !data
        ? "empty"
        : "live"

  const borderColor =
    alertLevel === "critical"
      ? "#ef4444"
      : alertLevel === "warning"
        ? "#f59e0b"
        : config.color

  return (
    <Card.Root
      borderWidth="2px"
      borderColor={borderColor}
      borderRadius="8px"
      padding="16px"
      backgroundColor="white"
      _hover={{ boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)" }}
      transition="box-shadow 200ms"
      role="article"
      aria-label={`${config.label} card`}
    >
      <Card.Header padding="0" marginBottom="12px">
        <Flex justifyContent="space-between" alignItems="center">
          <Flex alignItems="center" gap="8px">
            <Text fontSize="24px" role="img" aria-label={config.label}>
              {config.icon}
            </Text>
            <Box>
              <Text fontSize="16px" fontWeight="600" color="#111827">
                {config.label}
              </Text>
              <Text fontSize="12px" color="#6b7280">
                {config.description}
              </Text>
            </Box>
          </Flex>
          {onToggleTableView && (
            <Button
              size="sm"
              variant="outline"
              onClick={onToggleTableView}
              aria-label={`View ${config.label} data as ${showTableView ? "chart" : "table"}`}
              aria-expanded={showTableView}
              _focus={{ outline: "2px solid #3b82f6", outlineOffset: "4px" }}
            >
              {showTableView ? "View Chart" : "View Table"}
            </Button>
          )}
        </Flex>
      </Card.Header>

      <Card.Body padding="0">
        {state === "loading" && <LoadingState />}
        {state === "error" && (
          <ErrorState error={error!} onRetry={() => window.location.reload()} />
        )}
        {state === "empty" && <EmptyState ledgerType={ledgerType} />}
        {state === "live" && (
          <>
            {children}
            {data?.lastUpdated && (
              <Flex
                justifyContent="flex-end"
                marginTop="12px"
                alignItems="center"
                gap="4px"
              >
                <Box
                  width="8px"
                  height="8px"
                  borderRadius="50%"
                  backgroundColor="#22c55e"
                  animation="pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
                  aria-hidden="true"
                />
                <Text fontSize="12px" color="#6b7280">
                  Updated{" "}
                  {formatDistanceToNow(data.lastUpdated, { addSuffix: true })}
                </Text>
              </Flex>
            )}
          </>
        )}
      </Card.Body>
    </Card.Root>
  )
}

function LoadingState() {
  return (
    <Box aria-label="Loading data">
      <Skeleton height="200px" borderRadius="4px" marginBottom="12px" />
      <Flex gap="8px">
        <Skeleton height="60px" borderRadius="4px" flex="1" />
        <Skeleton height="60px" borderRadius="4px" flex="1" />
        <Skeleton height="60px" borderRadius="4px" flex="1" />
      </Flex>
    </Box>
  )
}

function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <Box
      textAlign="center"
      padding="32px"
      backgroundColor="#fef2f2"
      borderRadius="4px"
      role="alert"
      aria-live="assertive"
    >
      <Text fontSize="48px" marginBottom="8px" role="img" aria-label="Error">
        ⚠️
      </Text>
      <Text fontSize="16px" fontWeight="600" color="#ef4444" marginBottom="4px">
        Unable to load data
      </Text>
      <Text fontSize="14px" color="#6b7280" marginBottom="16px">
        {error.message || "An unexpected error occurred"}
      </Text>
      <Button
        colorScheme="red"
        onClick={onRetry}
        aria-label="Retry loading data"
        _focus={{ outline: "2px solid #ef4444", outlineOffset: "4px" }}
      >
        Retry
      </Button>
    </Box>
  )
}

function EmptyState({ ledgerType }: { ledgerType: string }) {
  return (
    <Box
      textAlign="center"
      padding="32px"
      backgroundColor="#f9fafb"
      borderRadius="4px"
      role="status"
    >
      <Text fontSize="48px" marginBottom="8px" role="img" aria-label="No data">
        📭
      </Text>
      <Text fontSize="16px" fontWeight="600" color="#111827" marginBottom="4px">
        No data available
      </Text>
      <Text fontSize="14px" color="#6b7280">
        No {ledgerType} data for selected time period.
        <br />
        Try expanding date range to 90 days.
      </Text>
    </Box>
  )
}
