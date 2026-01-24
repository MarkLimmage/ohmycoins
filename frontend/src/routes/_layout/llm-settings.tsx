import { Box, Button, Container, Heading } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import LLMCredentialForm from "@/components/Agent/LLMCredentialForm"
import LLMCredentialList from "@/components/Agent/LLMCredentialList"
import ProviderInfo from "@/components/Agent/ProviderInfo"

export const Route = createFileRoute("/_layout/llm-settings")({
  component: LLMSettings,
})

function LLMSettings() {
  const [showForm, setShowForm] = useState(false)

  return (
    <Container maxW="full">
      <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
        AI Provider Settings
      </Heading>

      <ProviderInfo />

      <Box mt={8}>
        {!showForm && (
          <Button
            variant="solid"
            colorPalette="blue"
            onClick={() => setShowForm(true)}
            mb={4}
          >
            Add Credential
          </Button>
        )}

        {showForm && <LLMCredentialForm onCancel={() => setShowForm(false)} />}

        <LLMCredentialList />
      </Box>
    </Container>
  )
}
