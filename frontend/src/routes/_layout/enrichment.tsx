import { Container } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { EnrichmentDashboard } from "@/features/enrichment/EnrichmentDashboard"

export const Route = createFileRoute("/_layout/enrichment")({
  component: EnrichmentPage,
})

function EnrichmentPage() {
  return (
    <Container maxW="full" py={8}>
      <EnrichmentDashboard />
    </Container>
  )
}
