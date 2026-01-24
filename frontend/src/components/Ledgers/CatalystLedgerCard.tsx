import { Badge, Box, Flex, Text } from "@chakra-ui/react"
import { formatDistanceToNow } from "date-fns"
import { LedgerCard } from "./LedgerCard"
import type { CatalystLedgerData, LedgerCardProps } from "./types"

/**
 * CatalystLedgerCard - Event list
 * Shows real-time events and alerts
 * REQ-UX-001, REQ-UX-004
 */
export function CatalystLedgerCard(props: LedgerCardProps) {
  const data = props.data as CatalystLedgerData | undefined

  return (
    <LedgerCard {...props}>
      {props.showTableView ? (
        <CatalystTableView data={data} />
      ) : (
        <CatalystListView data={data} onDrillDown={props.onDrillDown} />
      )}
    </LedgerCard>
  )
}

function CatalystListView({
  data,
  onDrillDown,
}: {
  data?: CatalystLedgerData
  onDrillDown?: (id: string) => void
}) {
  if (!data) return null

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "#ef4444"
      case "high":
        return "#f59e0b"
      case "medium":
        return "#3b82f6"
      default:
        return "#6b7280"
    }
  }

  const getPriorityBgColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "#fef2f2"
      case "high":
        return "#fffbeb"
      case "medium":
        return "#eff6ff"
      default:
        return "#f9fafb"
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "listing":
        return "🎉"
      case "regulation":
        return "⚖️"
      case "upgrade":
        return "🔧"
      default:
        return "📌"
    }
  }

  return (
    <Box>
      {data.events.length === 0 ? (
        <Box
          textAlign="center"
          padding="48px 16px"
          backgroundColor="#f9fafb"
          borderRadius="4px"
        >
          <Text fontSize="48px" marginBottom="8px">
            ✨
          </Text>
          <Text fontSize="14px" color="#6b7280">
            No recent events
          </Text>
        </Box>
      ) : (
        <Box
          maxHeight="400px"
          overflowY="auto"
          role="region"
          aria-label="Catalyst events list"
          tabIndex={0}
        >
          <Flex flexDirection="column" gap="12px">
            {data.events.slice(0, 10).map((event) => (
              <Box
                key={event.id}
                padding="12px"
                backgroundColor={getPriorityBgColor(event.priority)}
                borderRadius="4px"
                borderLeft={`4px solid ${getPriorityColor(event.priority)}`}
                cursor={onDrillDown ? "pointer" : "default"}
                onClick={() => onDrillDown?.(event.id)}
                _hover={onDrillDown ? { backgroundColor: "#f3f4f6" } : {}}
                _focus={{ outline: "2px solid #f59e0b", outlineOffset: "4px" }}
                tabIndex={0}
                role="article"
                aria-label={`${event.priority} priority ${event.type} event: ${event.title}`}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && onDrillDown) {
                    e.preventDefault()
                    onDrillDown(event.id)
                  }
                }}
              >
                <Flex
                  justifyContent="space-between"
                  alignItems="flex-start"
                  marginBottom="8px"
                >
                  <Flex alignItems="center" gap="8px" flex="1">
                    <Text fontSize="20px" role="img" aria-label={event.type}>
                      {getTypeIcon(event.type)}
                    </Text>
                    <Text fontSize="14px" fontWeight="600" color="#111827">
                      {event.title}
                    </Text>
                  </Flex>
                  <Badge
                    backgroundColor={getPriorityColor(event.priority)}
                    color="white"
                    paddingX="8px"
                    paddingY="2px"
                    borderRadius="4px"
                    fontSize="12px"
                    fontWeight="600"
                    textTransform="uppercase"
                  >
                    {event.priority}
                  </Badge>
                </Flex>
                {event.description && (
                  <Text fontSize="13px" color="#6b7280" marginBottom="8px">
                    {event.description}
                  </Text>
                )}
                <Flex justifyContent="space-between" alignItems="center">
                  <Text fontSize="12px" color="#6b7280">
                    {formatDistanceToNow(event.timestamp, { addSuffix: true })}
                  </Text>
                  <Badge
                    backgroundColor="#f3f4f6"
                    color="#6b7280"
                    paddingX="8px"
                    paddingY="2px"
                    borderRadius="4px"
                    fontSize="11px"
                    textTransform="capitalize"
                  >
                    {event.type}
                  </Badge>
                </Flex>
              </Box>
            ))}
          </Flex>
        </Box>
      )}
    </Box>
  )
}

function CatalystTableView({ data }: { data?: CatalystLedgerData }) {
  if (!data) return null

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)
  }

  return (
    <Box
      overflowX="auto"
      role="region"
      aria-label="Catalyst events data table"
      tabIndex={0}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Event
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Type
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "left",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Priority
            </th>
            <th
              style={{
                padding: "12px",
                textAlign: "right",
                fontSize: "12px",
                fontWeight: 600,
                color: "#6b7280",
              }}
            >
              Time
            </th>
          </tr>
        </thead>
        <tbody>
          {data.events.slice(0, 10).map((event, index, array) => (
            <tr
              key={event.id}
              style={{
                borderBottom:
                  index === array.length - 1 ? "none" : "1px solid #f3f4f6",
              }}
            >
              <td
                style={{ padding: "12px", fontSize: "14px", fontWeight: 500 }}
              >
                {event.title}
              </td>
              <td
                style={{
                  padding: "12px",
                  fontSize: "14px",
                  textTransform: "capitalize",
                }}
              >
                {event.type}
              </td>
              <td
                style={{
                  padding: "12px",
                  fontSize: "14px",
                  fontWeight: 500,
                  textTransform: "uppercase",
                }}
              >
                <span
                  style={{
                    color:
                      event.priority === "critical"
                        ? "#ef4444"
                        : event.priority === "high"
                          ? "#f59e0b"
                          : event.priority === "medium"
                            ? "#3b82f6"
                            : "#6b7280",
                  }}
                >
                  {event.priority}
                </span>
              </td>
              <td
                style={{
                  padding: "12px",
                  textAlign: "right",
                  fontSize: "13px",
                  color: "#6b7280",
                }}
              >
                {formatDate(event.timestamp)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  )
}
