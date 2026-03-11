import { Badge, Box, HStack, Text, VStack, IconButton } from "@chakra-ui/react"
import { formatDistanceToNow } from "date-fns"
import { FiTrash2 } from "react-icons/fi"
import type { AgentSessionPublic } from "@/client"

interface SessionListProps {
  sessions: AgentSessionPublic[]
  selectedId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

const statusConfig: Record<string, { color: string; label: string }> = {
  pending: { color: "yellow", label: "Pending" },
  running: { color: "blue", label: "Running" },
  completed: { color: "green", label: "Completed" },
  failed: { color: "red", label: "Failed" },
  cancelled: { color: "gray", label: "Cancelled" },
}

export function SessionList({
  sessions,
  selectedId,
  onSelect,
  onDelete,
}: SessionListProps) {
  if (sessions.length === 0) {
    return (
      <Box
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="whiteAlpha.200"
        bg="gray.900"
      >
        <Text color="gray.500" fontSize="sm" textAlign="center">
          No sessions yet. Create one to get started.
        </Text>
      </Box>
    )
  }

  return (
    <VStack
      align="stretch"
      gap={0}
      borderRadius="lg"
      border="1px solid"
      borderColor="whiteAlpha.200"
      bg="gray.900"
      overflow="hidden"
      maxH="600px"
      overflowY="auto"
    >
      <Box px={3} py={2} borderBottom="1px solid" borderColor="whiteAlpha.200">
        <Text fontSize="xs" fontWeight="bold" color="gray.300">
          Sessions ({sessions.length})
        </Text>
      </Box>
      {sessions.map((session) => {
        const config = statusConfig[session.status] || statusConfig.pending
        const isSelected = session.id === selectedId
        const timeAgo = session.created_at
          ? formatDistanceToNow(new Date(session.created_at), {
              addSuffix: true,
            })
          : ""

        return (
          <Box
            key={session.id}
            px={3}
            py={3}
            cursor="pointer"
            onClick={() => onSelect(session.id)}
            bg={isSelected ? "whiteAlpha.100" : "transparent"}
            borderLeft={isSelected ? "3px solid" : "3px solid transparent"}
            borderColor={isSelected ? "blue.400" : "transparent"}
            _hover={{ bg: "whiteAlpha.50" }}
            borderBottom="1px solid"
            borderBottomColor="whiteAlpha.100"
          >
            <VStack align="stretch" gap={1}>
              <HStack justify="space-between">
                <Text fontSize="sm" fontWeight="medium" lineClamp={1} flex={1} color="gray.100">
                  {session.user_goal}
                </Text>
                <HStack gap={1}>
                  <Badge
                    colorPalette={config.color}
                    size="sm"
                    variant="subtle"
                    flexShrink={0}
                  >
                    {config.label}
                  </Badge>
                  <IconButton
                    aria-label="Delete session"
                    size="xs"
                    variant="ghost"
                    colorPalette="red"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (window.confirm("Are you sure you want to delete this session?")) {
                        onDelete(session.id)
                      }
                    }}
                  >
                    <FiTrash2 />
                  </IconButton>
                </HStack>
              </HStack>
              <HStack justify="space-between">
                <Text fontSize="xs" color="gray.400" fontFamily="mono">
                  {session.id.slice(0, 8)}
                </Text>
                <Text fontSize="xs" color="gray.400">
                  {timeAgo}
                </Text>
              </HStack>
              {session.error_message && (
                <Text fontSize="xs" color="red.400" lineClamp={1}>
                  {session.error_message}
                </Text>
              )}
            </VStack>
          </Box>
        )
      })}
    </VStack>
  )
}
