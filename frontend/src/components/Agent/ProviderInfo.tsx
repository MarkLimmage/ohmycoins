import {
  Box,
  Heading,
  Link,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"

const ProviderInfo = () => {
  return (
    <Box mb={8} p={6} bg="bg.muted" borderRadius="md">
      <VStack align="start" gap={4}>
        <Heading size="sm">Supported AI Providers</Heading>
        <Text fontSize="sm" color="fg.muted">
          Connect your own API keys to use different AI models. Your credentials
          are encrypted and stored securely.
        </Text>

        <Table.Root size="sm" variant="outline">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Provider</Table.ColumnHeader>
              <Table.ColumnHeader>Default Model</Table.ColumnHeader>
              <Table.ColumnHeader>Documentation</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            <Table.Row>
              <Table.Cell fontWeight="medium">OpenAI</Table.Cell>
              <Table.Cell>gpt-4o-mini</Table.Cell>
              <Table.Cell>
                <Link
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  color="blue.500"
                >
                  Get API Key
                </Link>
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell fontWeight="medium">Google Gemini</Table.Cell>
              <Table.Cell>gemini-1.5-flash</Table.Cell>
              <Table.Cell>
                <Link
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  color="blue.500"
                >
                  Get API Key
                </Link>
              </Table.Cell>
            </Table.Row>
            <Table.Row>
              <Table.Cell fontWeight="medium">Anthropic Claude</Table.Cell>
              <Table.Cell>claude-3-5-sonnet-20241022</Table.Cell>
              <Table.Cell>
                <Link
                  href="https://console.anthropic.com/settings/keys"
                  target="_blank"
                  color="blue.500"
                >
                  Get API Key
                </Link>
              </Table.Cell>
            </Table.Row>
          </Table.Body>
        </Table.Root>
      </VStack>
    </Box>
  )
}

export default ProviderInfo
