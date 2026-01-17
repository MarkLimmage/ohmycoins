import {
  Badge,
  Box,
  Button,
  Card,
  Flex,
  HStack,
  Heading,
  Icon,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { SiAnthropic, SiGoogle, SiOpenai } from "react-icons/si"

import {
  type ApiError,
  type UserLLMCredentialPublic,
  UsersService,
} from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const getProviderIcon = (provider: string) => {
  const providerLower = provider.toLowerCase()
  if (providerLower.includes("openai")) return SiOpenai
  if (providerLower.includes("google") || providerLower.includes("gemini"))
    return SiGoogle
  if (providerLower.includes("anthropic") || providerLower.includes("claude"))
    return SiAnthropic
  return null
}

const getProviderColor = (provider: string) => {
  const providerLower = provider.toLowerCase()
  if (providerLower.includes("openai")) return "teal"
  if (providerLower.includes("google") || providerLower.includes("gemini"))
    return "blue"
  if (providerLower.includes("anthropic") || providerLower.includes("claude"))
    return "orange"
  return "gray"
}

const LLMCredentialList = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    data: credentials,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["llmCredentials"],
    queryFn: () => UsersService.getLlmCredentialsApiV1UsersMeLlmCredentialsGet(),
  })

  const deleteMutation = useMutation({
    mutationFn: (credentialId: string) =>
      UsersService.deleteLlmCredentialApiV1UsersMeLlmCredentialsCredentialIdDelete(
        { credentialId },
      ),
    onSuccess: () => {
      showSuccessToast("Credential deleted successfully.")
      queryClient.invalidateQueries({ queryKey: ["llmCredentials"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const setDefaultMutation = useMutation({
    mutationFn: (credentialId: string) =>
      UsersService.setDefaultLlmCredentialApiV1UsersMeLlmCredentialsCredentialIdDefaultPut(
        { credentialId },
      ),
    onSuccess: () => {
      showSuccessToast("Default credential updated.")
      queryClient.invalidateQueries({ queryKey: ["llmCredentials"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="200px">
        <Spinner size="lg" />
      </Flex>
    )
  }

  if (error) {
    return (
      <Box p={4} bg="red.50" borderRadius="md">
        <Text color="red.500">Failed to load credentials</Text>
      </Box>
    )
  }

  if (!credentials || credentials.length === 0) {
    return (
      <Box p={8} textAlign="center" bg="bg.muted" borderRadius="md">
        <Text color="fg.muted">
          No credentials configured yet. Add one to get started.
        </Text>
      </Box>
    )
  }

  return (
    <VStack gap={4} align="stretch" mt={4}>
      <Heading size="sm">Your Credentials</Heading>
      {credentials.map((credential: UserLLMCredentialPublic) => {
        const ProviderIcon = getProviderIcon(credential.provider_name)
        const providerColor = getProviderColor(credential.provider_name)

        return (
          <Card.Root key={credential.id} variant="outline">
            <Card.Body>
              <Flex justify="space-between" align="start" gap={4}>
                <HStack gap={4} flex={1}>
                  {ProviderIcon && (
                    <Icon
                      as={ProviderIcon}
                      boxSize={8}
                      color={`${providerColor}.500`}
                    />
                  )}
                  <VStack align="start" gap={1} flex={1}>
                    <HStack>
                      <Text fontWeight="semibold" fontSize="lg">
                        {credential.provider_name}
                      </Text>
                      {credential.is_default && (
                        <Badge colorPalette="blue" variant="solid">
                          Default
                        </Badge>
                      )}
                    </HStack>
                    {credential.model_name && (
                      <Text fontSize="sm" color="fg.muted">
                        Model: {credential.model_name}
                      </Text>
                    )}
                    <Text fontSize="xs" color="fg.muted">
                      Added:{" "}
                      {new Date(credential.created_at).toLocaleDateString()}
                    </Text>
                  </VStack>
                </HStack>

                <HStack gap={2}>
                  {!credential.is_default && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setDefaultMutation.mutate(credential.id)}
                      loading={setDefaultMutation.isPending}
                    >
                      Set Default
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    colorPalette="red"
                    onClick={() => deleteMutation.mutate(credential.id)}
                    loading={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </HStack>
              </Flex>
            </Card.Body>
          </Card.Root>
        )
      })}
    </VStack>
  )
}

export default LLMCredentialList
