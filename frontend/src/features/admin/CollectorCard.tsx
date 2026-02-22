import { 
  Box, 
  Card, 
  Flex, 
  Heading, 
  Text, 
  Badge, 
  IconButton,
  Stat
} from "@chakra-ui/react"
import { FiPlay, FiPause, FiTrash2, FiEdit, FiZap } from "react-icons/fi"
import { Tooltip } from "@/components/ui/tooltip"
import { LineChart, Line, ResponsiveContainer } from "recharts"
import { CollectorInstance } from "./types"
import { useCollectorStats } from "./hooks"

interface CollectorCardProps {
  instance: CollectorInstance
  pluginName: string
  onEdit: () => void
  onToggle: () => void
  onRun: () => void
  onDelete: () => void
}

export const CollectorCard = ({ instance, pluginName, onEdit, onToggle, onRun, onDelete }: CollectorCardProps) => {
  const { data: stats } = useCollectorStats(instance.id)

  const latestCount = stats && stats.length > 0 ? stats[stats.length - 1].count : 0

  return (
    <Card.Root>
      <Card.Body>
        <Flex justify="space-between" align="start" mb={2}>
           <Box>
             <Heading size="sm" mb={1}>{instance.name}</Heading>
             <Text fontSize="xs" color="gray.500">{pluginName}</Text>
             <Text fontSize="xs" fontFamily="monospace" color="gray.400">{instance.schedule_cron}</Text>
           </Box>
           <Badge colorScheme={instance.status === 'success' ? 'green' : instance.status === 'failed' ? 'red' : 'gray'}>
             {instance.status}
           </Badge>
        </Flex>

        <Box height="80px" my={4}>
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

        <Flex justify="space-between" align="center">
            <Stat.Root size="sm">
                <Stat.Label>Last Run</Stat.Label>
                <Stat.ValueText>
                    {instance.last_run ? new Date(instance.last_run).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Never'}
                </Stat.ValueText>
                <Stat.HelpText>
                    {latestCount} items
                </Stat.HelpText>
            </Stat.Root>

            <Flex gap={1}>
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
                
                <Tooltip content={instance.is_active ? "Pause" : "Resume"}>
                  <IconButton 
                    aria-label={instance.is_active ? "Pause" : "Resume"}
                    size="sm" 
                    variant="ghost"
                    colorScheme={instance.is_active ? "orange" : "green"}
                    onClick={onToggle}
                  >
                    {instance.is_active ? <FiPause /> : <FiPlay />}
                  </IconButton>
                </Tooltip>

                <Tooltip content="Delete">
                  <IconButton 
                    aria-label="Delete"
                    size="sm" 
                    variant="ghost" 
                    colorScheme="red"
                    onClick={onDelete}
                  >
                    <FiTrash2 />
                  </IconButton>
                </Tooltip>
            </Flex>
        </Flex>
      </Card.Body>
    </Card.Root>
  )
}
