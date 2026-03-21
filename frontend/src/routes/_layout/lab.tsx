import { Container } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { LabDashboard } from "@/features/lab/LabDashboard"

export const Route = createFileRoute("/_layout/lab")({
  component: LabPage,
})

function LabPage() {
  return (
    <Container maxW="full" py={2} px={2}>
      <LabDashboard />
    </Container>
  )
}
