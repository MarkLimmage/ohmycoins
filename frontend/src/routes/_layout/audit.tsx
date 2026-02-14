import { Badge, Container, Heading, Table, Text, Box, Tabs } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"

import { AuditService, RiskService } from "@/client"
import {
  PaginationItems,
  PaginationNextTrigger,
  PaginationPrevTrigger,
  PaginationRoot,
} from "@/components/ui/pagination"

const auditSearchSchema = z.object({
  page: z.number().catch(1),
})

const PER_PAGE = 20

function getAuditQueryOptions({ page }: { page: number }) {
  return {
    queryFn: () =>
      AuditService.readTradeAudits({ skip: (page - 1) * PER_PAGE, limit: PER_PAGE }),
    queryKey: ["audit", { page }],
  }
}

function getKillSwitchHistoryQueryOptions() {
  return {
    queryFn: () => RiskService.readAuditLogs({ eventType: "kill_switch_toggle", limit: 50 }),
    queryKey: ["risk", "audit", "kill_switch"],
  }
}

export const Route = createFileRoute("/_layout/audit")({
  component: Audit,
  validateSearch: (search) => auditSearchSchema.parse(search),
})

function Audit() {
  const { page } = Route.useSearch()
  const navigate = Route.useNavigate()

  const { data, isLoading } = useQuery({
    ...getAuditQueryOptions({ page }),
    placeholderData: (prevData) => prevData,
  })

  // Kill Switch Logs
  const { data: ksData, isLoading: ksLoading } = useQuery({
    ...getKillSwitchHistoryQueryOptions(),
  })

  const records = data?.data ?? []
  const count = data?.count ?? 0
  
  const ksRecords = ksData?.data ?? []

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} pt={12}>
        Audit Logs
      </Heading>
      <Text fontSize="sm" color="gray.500" mb={8}>
        System transparency and accountability records.
      </Text>

      <Tabs.Root defaultValue="trades">
        <Tabs.List>
          <Tabs.Trigger value="trades">
            Trade Decisions
          </Tabs.Trigger>
          <Tabs.Trigger value="killswitch">
            Kill Switch History
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="trades">
          {isLoading ? (
            <Text>Loading...</Text>
          ) : (
            <Box overflowX="auto">
              <Table.Root size="sm" striped>
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                    <Table.ColumnHeader>Agent ID</Table.ColumnHeader>
                    <Table.ColumnHeader>Asset</Table.ColumnHeader>
                    <Table.ColumnHeader>Decision</Table.ColumnHeader>
                    <Table.ColumnHeader>Confidence</Table.ColumnHeader>
                    <Table.ColumnHeader>Reason</Table.ColumnHeader>
                    <Table.ColumnHeader>Status</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {records.map((record) => (
                    <Table.Row key={record.id}>
                      <Table.Cell whiteSpace="nowrap">
                        {new Date(record.timestamp).toLocaleString()}
                      </Table.Cell>
                      <Table.Cell>{record.agent_id}</Table.Cell>
                      <Table.Cell fontWeight="bold">{record.asset}</Table.Cell>
                      <Table.Cell>
                        <Badge
                          colorScheme={
                            record.decision === "BUY"
                              ? "green"
                              : record.decision === "SELL"
                                ? "red"
                                : "gray"
                          }
                        >
                          {record.decision}
                        </Badge>
                      </Table.Cell>
                      <Table.Cell>{((record.confidence_score ?? 0) * 100).toFixed(1)}%</Table.Cell>
                      <Table.Cell maxW="md" truncate title={record.reason}>
                        {record.reason}
                      </Table.Cell>
                      <Table.Cell>
                        {record.is_executed ? (
                          <Badge colorScheme="green">Executed</Badge>
                        ) : record.block_reason ? (
                          <Badge colorScheme="red" title={record.block_reason}>
                            Blocked: {record.block_reason}
                          </Badge>
                        ) : (
                          <Badge>Pending</Badge>
                        )}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
              
              <PaginationRoot
                count={count}
                pageSize={PER_PAGE}
                page={page}
                onPageChange={(e) =>
                  navigate({
                    search: (prev) => ({ ...prev, page: e.page }),
                  })
                }
                my={4}
              >
                <PaginationPrevTrigger />
                <PaginationItems />
                <PaginationNextTrigger />
              </PaginationRoot>
            </Box>
          )}
        </Tabs.Content>

        <Tabs.Content value="killswitch">
          {ksLoading ? (
             <Text>Loading...</Text>
          ) : (
            <Box overflowX="auto">
              <Table.Root size="sm" striped>
                <Table.Header>
                  <Table.Row>
                    <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                    <Table.ColumnHeader>User</Table.ColumnHeader>
                    <Table.ColumnHeader>Action</Table.ColumnHeader>
                    <Table.ColumnHeader>Details</Table.ColumnHeader>
                  </Table.Row>
                </Table.Header>
                 <Table.Body>
                  {ksRecords.map((record) => (
                    <Table.Row key={record.id}>
                      <Table.Cell whiteSpace="nowrap">
                        {new Date(record.timestamp).toLocaleString()}
                      </Table.Cell>
                      <Table.Cell>{record.user_id}</Table.Cell>
                      <Table.Cell>
                        <Badge colorScheme="purple">TOGGLE</Badge>
                      </Table.Cell>
                      <Table.Cell>
                        <Text as="pre" fontSize="xs">
                            {JSON.stringify(record.details, null, 2)}
                        </Text>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table.Root>
            </Box>
          )}
        </Tabs.Content>
      </Tabs.Root>
    </Container>
  )
}
