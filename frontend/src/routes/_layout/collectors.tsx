import { Container } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { CollectorDashboard } from "@/features/admin/CollectorDashboard"

export const Route = createFileRoute("/_layout/collectors")({
  component: CollectorsPage,
})

function CollectorsPage() {
  return (
    <Container maxW="full">
      <CollectorDashboard />
    </Container>
  )
}
