import { Box, Container, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { CollectorDashboard } from "@/features/admin/CollectorDashboard"
import { CollectorHealth } from "@/features/dashboard/CollectorHealth"

export const Route = createFileRoute("/_layout/collectors")({
  component: CollectorsPage,
})

function CollectorsPage() {
  return (
    <Container maxW="full" py={8}>
      <VStack gap={8} align="stretch">
        <Box>
          <CollectorHealth />
        </Box>
        <Box>
          <CollectorDashboard />
        </Box>
      </VStack>
    </Container>
  )
}
