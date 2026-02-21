import { Box, Card, Heading, Icon, Stat, Text, Stack, Spinner } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiDatabase } from "react-icons/fi"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts"

import { OpenAPI } from "@/client"

interface CollectorStat {
  timestamp: string
  records_collected: number
}

const fetchCollectorStats = async (): Promise<CollectorStat[]> => {
  const baseUrl = OpenAPI.BASE || "http://localhost:8040/api/v1"
  const url = `${baseUrl}/mock/collectors/stats` 
  const token = localStorage.getItem("access_token")
  
  const response = await fetch(url, {
      headers: {
          'Authorization': `Bearer ${token}`
      }
  })
  if (!response.ok) {
    throw new Error("Failed to fetch collector stats")
  }
  return response.json()
}

export function CollectorThroughput() {
  const { data: stats, isLoading } = useQuery({
    queryFn: fetchCollectorStats,
    queryKey: ["collectors", "stats"],
    // Refresh every minute
    refetchInterval: 60000 
  })

  // Calculate total items in last hour
  const totalItems = stats?.reduce((acc, curr) => acc + curr.records_collected, 0) || 0
  const avgPerMinute = stats && stats.length > 0 ? (totalItems / stats.length).toFixed(1) : 0

  if (isLoading) {
      return (
          <Card.Root variant="outline">
              <Card.Body>
                  <Stack align="center" justify="center" h="100px">
                      <Spinner size="sm" />
                  </Stack>
              </Card.Body>
          </Card.Root>
      )
  }

  return (
    <Card.Root variant="outline">
      <Card.Body p={4} display="flex" flexDirection="column" height="100%">
        <Stat.Root mb={4}>
          <Stat.Label color="gray.500" display="flex" alignItems="center" gap={2}>
            <Icon as={FiDatabase} />
            Data Throughput
          </Stat.Label>
          <Stat.ValueText fontWeight="bold" fontSize="2xl">
            {totalItems.toLocaleString()} <Text as="span" fontSize="sm" color="gray.500" fontWeight="normal">items/hr</Text>
          </Stat.ValueText>
          <Stat.HelpText>
             ~{avgPerMinute} items/min
          </Stat.HelpText>
        </Stat.Root>
        
        <Box height="60px" width="100%" flex="1">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats}>
                    <defs>
                        <linearGradient id="colorRecords" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3182ce" stopOpacity={0.8}/>
                            <stop offset="95%" stopColor="#3182ce" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <Tooltip 
                        contentStyle={{ fontSize: '12px', padding: '5px' }}
                        labelFormatter={(label) => new Date(label).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    />
                    <Area 
                        type="monotone" 
                        dataKey="records_collected" 
                        stroke="#3182ce" 
                        fillOpacity={1} 
                        fill="url(#colorRecords)" 
                        isAnimationActive={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </Box>
      </Card.Body>
    </Card.Root>
  )
}
