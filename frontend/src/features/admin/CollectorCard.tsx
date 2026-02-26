import {
  Box,
  Card,
  Flex,
  Heading,
  HStack,
  IconButton,
  SimpleGrid,
  Switch,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiEdit, FiZap } from "react-icons/fi"
import { Line, LineChart, ResponsiveContainer } from "recharts"
import { Tooltip } from "@/components/ui/tooltip"
import { useCollectorStats } from "./hooks"
import type { CollectorCardData } from "./types"

interface CollectorCardProps {
  card: CollectorCardData
  onEdit: () => void
  onToggle: () => void
  onRun: () => void
}

export const CollectorCard = ({
  card,
  onEdit,
  onToggle,
  onRun,
}: CollectorCardProps) => {
  const { data: stats } = useCollectorStats(
    card.instance_id ?? "",
    card.instance_id !== null,
  )

  const isConfigured = card.instance_id !== null
  const hasStats = card.total_runs !== null && card.total_runs > 0

  return (
    <Card.Root
      opacity={isConfigured ? 1 : 0.75}
      borderStyle={isConfigured ? "solid" : "dashed"}
    >
      <Card.Body>
        {/* Header: Plugin name + description + Switch */}
        <Flex justify="space-between" align="start" mb={4}>
          <VStack align="start" gap={1} flex={1}>
            <Heading size="sm">{card.plugin_name}</Heading>
            <Text fontSize="xs" color="gray.600">
              {isConfigured ? card.schedule_cron : card.plugin_description}
            </Text>
          </VStack>
          <Switch.Root checked={card.is_active} onCheckedChange={onToggle}>
            <Switch.HiddenInput />
            <Switch.Control>
              <Switch.Thumb />
            </Switch.Control>
          </Switch.Root>
        </Flex>

        {/* Stats row - only when card has runs */}
        {hasStats && (
          <SimpleGrid columns={2} gap={3} mb={4}>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Success Rate
              </Text>
              <Text fontSize="sm" fontWeight="bold">
                {(card.success_rate ?? 0).toFixed(1)}%
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Total Records
              </Text>
              <Text fontSize="sm" fontWeight="bold">
                {card.total_records ?? 0}
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Avg Duration
              </Text>
              <Text fontSize="sm" fontWeight="bold">
                {(card.avg_duration ?? 0).toFixed(2)}s
              </Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="gray.500">
                Total Runs
              </Text>
              <Text fontSize="sm" fontWeight="bold">
                {card.total_runs ?? 0}
              </Text>
            </Box>
          </SimpleGrid>
        )}

        {/* Sparkline - only when instance exists */}
        {isConfigured && (
          <Box height="60px" my={4}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats || []}>
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3771c8"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        )}

        {/* Action buttons - only when instance exists */}
        {isConfigured && (
          <HStack justify="flex-end" gap={1}>
            <Tooltip content="Run Now">
              <IconButton
                aria-label="Run Manual Trigger"
                size="sm"
                variant="ghost"
                colorScheme="blue"
                onClick={onRun}
              >
                <FiZap />
              </IconButton>
            </Tooltip>

            <Tooltip content="Edit">
              <IconButton
                aria-label="Edit"
                size="sm"
                variant="ghost"
                onClick={onEdit}
              >
                <FiEdit />
              </IconButton>
            </Tooltip>
          </HStack>
        )}
      </Card.Body>
    </Card.Root>
  )
}
