import {
  Accordion,
  Badge,
  Box,
  Button,
  DialogTitle,
  Flex,
  Heading,
  HStack,
  Icon,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { FiTrash2 } from "react-icons/fi"
import { SiAnthropic, SiGoogle, SiOpenai } from "react-icons/si"

import {
  type ApiError,
  type UserLLMCredentialsPublic,
  UsersService,
} from "@/client"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
} from "@/components/ui/dialog"
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

const getProviderLabel = (provider: string) => {
  const providerLower = provider.toLowerCase()
  if (providerLower.includes("openai")) return "OpenAI"
  if (providerLower.includes("google") || providerLower.includes("gemini"))
    return "Google"
  if (providerLower.includes("anthropic") || providerLower.includes("claude"))
    return "Anthropic"
  return provider
}

const LLMCredentialList = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [deleteTarget, setDeleteTarget] =
    useState<UserLLMCredentialsPublic | null>(null)

  const {
    data: credentials,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["llmCredentials"],
    queryFn: () => UsersService.listLlmCredentials(),
  })

  const deleteMutation = useMutation({
    mutationFn: (credentialId: string) =>
      UsersService.deleteLlmCredential({ credentialId }),
    onSuccess: () => {
      showSuccessToast("Credential deleted successfully.")
      setDeleteTarget(null)
      queryClient.invalidateQueries({ queryKey: ["llmCredentials"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const setDefaultMutation = useMutation({
    mutationFn: (credentialId: string) =>
      UsersService.setDefaultLlmCredential({ credentialId }),
    onSuccess: () => {
      showSuccessToast("Default credential updated.")
      queryClient.invalidateQueries({ queryKey: ["llmCredentials"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const grouped = useMemo(() => {
    if (!credentials) return {}
    const groups: Record<string, UserLLMCredentialsPublic[]> = {}
    for (const cred of credentials) {
      const key = cred.provider.toLowerCase()
      if (!groups[key]) groups[key] = []
      groups[key].push(cred)
    }
    return groups
  }, [credentials])

  const providerKeys = useMemo(() => Object.keys(grouped), [grouped])

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

      <Accordion.Root multiple defaultValue={providerKeys} collapsible>
        {providerKeys.map((providerKey) => {
          const creds = grouped[providerKey]
          const ProviderIcon = getProviderIcon(providerKey)
          const providerColor = getProviderColor(providerKey)
          const providerLabel = getProviderLabel(providerKey)

          return (
            <Accordion.Item key={providerKey} value={providerKey} border="none">
              <h2>
                <Accordion.ItemTrigger>
                  <HStack flex="1" gap={3}>
                    {ProviderIcon && (
                      <Icon
                        as={ProviderIcon}
                        boxSize={5}
                        color={`${providerColor}.500`}
                      />
                    )}
                    <Text fontWeight="semibold">{providerLabel}</Text>
                    <Badge colorPalette={providerColor} variant="subtle">
                      {creds.length}
                    </Badge>
                  </HStack>
                  <Accordion.ItemIndicator />
                </Accordion.ItemTrigger>
              </h2>
              <Accordion.ItemContent pb={2}>
                <VStack gap={2} align="stretch" pl={2}>
                  {creds.map((credential) => (
                    <Box
                      key={credential.id}
                      p={3}
                      borderWidth="1px"
                      borderRadius="md"
                    >
                      <Flex justify="space-between" align="start" gap={4}>
                        <VStack align="start" gap={1} flex={1}>
                          <HStack>
                            <Text fontWeight="medium">
                              {credential.model_name || "Default model"}
                            </Text>
                            {credential.is_default && (
                              <Badge colorPalette="blue" variant="solid">
                                Default
                              </Badge>
                            )}
                          </HStack>
                          <Text fontSize="xs" color="fg.muted">
                            Key: {credential.api_key_masked}
                          </Text>
                          <HStack gap={3}>
                            <Text fontSize="xs" color="fg.muted">
                              Added:{" "}
                              {new Date(
                                credential.created_at,
                              ).toLocaleDateString()}
                            </Text>
                            {credential.last_validated_at && (
                              <Text fontSize="xs" color="fg.muted">
                                Validated:{" "}
                                {new Date(
                                  credential.last_validated_at,
                                ).toLocaleDateString()}
                              </Text>
                            )}
                          </HStack>
                        </VStack>

                        <HStack gap={2}>
                          {!credential.is_default && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() =>
                                setDefaultMutation.mutate(credential.id)
                              }
                              loading={setDefaultMutation.isPending}
                            >
                              Set Default
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            colorPalette="red"
                            onClick={() => setDeleteTarget(credential)}
                          >
                            <FiTrash2 />
                            Delete
                          </Button>
                        </HStack>
                      </Flex>
                    </Box>
                  ))}
                </VStack>
              </Accordion.ItemContent>
            </Accordion.Item>
          )
        })}
      </Accordion.Root>

      {/* Delete confirmation dialog */}
      <DialogRoot
        size={{ base: "xs", md: "md" }}
        placement="center"
        role="alertdialog"
        open={!!deleteTarget}
        onOpenChange={({ open }) => {
          if (!open) setDeleteTarget(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Credential</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text>
              Are you sure you want to delete the{" "}
              <strong>
                {deleteTarget?.model_name || deleteTarget?.provider}
              </strong>{" "}
              credential? This action cannot be undone.
            </Text>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              loading={deleteMutation.isPending}
              onClick={() => {
                if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
              }}
            >
              Delete
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </DialogContent>
      </DialogRoot>
    </VStack>
  )
}

export default LLMCredentialList
