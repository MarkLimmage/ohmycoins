import {
  Box,
  Button,
  Card,
  Flex,
  HStack,
  Heading,
  Input,
  Text,
  VStack,
  createListCollection,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiAlertCircle, FiCheck, FiEye, FiEyeOff, FiKey } from "react-icons/fi"

import {
  type ApiError,
  type UserLLMCredentialCreate,
  UsersService,
} from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Checkbox } from "../ui/checkbox"
import { Field } from "../ui/field"
import { InputGroup } from "../ui/input-group"
import {
  SelectContent,
  SelectItem,
  SelectRoot,
  SelectTrigger,
  SelectValueText,
} from "../ui/select"

interface LLMCredentialFormProps {
  onCancel: () => void
}

interface FormData {
  provider_name: string
  api_key_encrypted: string
  model_name?: string
  is_default: boolean
}

const providers = createListCollection({
  items: [
    { label: "OpenAI", value: "openai" },
    { label: "Google Gemini", value: "google" },
    { label: "Anthropic Claude", value: "anthropic" },
  ],
})

const LLMCredentialForm = ({ onCancel }: LLMCredentialFormProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [showApiKey, setShowApiKey] = useState(false)
  const [validationResult, setValidationResult] = useState<{
    valid: boolean
    message?: string | null
  } | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    mode: "onBlur",
    defaultValues: {
      is_default: false,
    },
  })

  const selectedProvider = watch("provider_name")
  const apiKey = watch("api_key_encrypted")

  const createMutation = useMutation({
    mutationFn: (data: UserLLMCredentialCreate) =>
      UsersService.createLlmCredentialApiV1UsersMeLlmCredentialsPost({
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Credential added successfully.")
      queryClient.invalidateQueries({ queryKey: ["llmCredentials"] })
      onCancel()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const validateCredential = async () => {
    const provider = selectedProvider
    const key = apiKey

    if (!provider || !key) {
      showErrorToast("Please select a provider and enter an API key.")
      return
    }

    setIsValidating(true)
    setValidationResult(null)

    try {
      const result =
        await UsersService.validateLlmCredentialsApiV1UsersMeLlmCredentialsValidatePost(
          {
            requestBody: {
              provider_name: provider,
              api_key_encrypted: key,
            },
          },
        )

      setValidationResult(result)

      if (result.valid) {
        showSuccessToast("Credential validated successfully!")
      } else {
        showErrorToast(result.message || "Validation failed")
      }
    } catch (err) {
      handleError(err as ApiError)
      setValidationResult({ valid: false, message: "Validation failed" })
    } finally {
      setIsValidating(false)
    }
  }

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    const payload: UserLLMCredentialCreate = {
      provider_name: data.provider_name,
      api_key_encrypted: data.api_key_encrypted,
      model_name: data.model_name || undefined,
      is_default: data.is_default,
    }
    createMutation.mutate(payload)
  }

  const getPlaceholderModel = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case "openai":
        return "gpt-4o-mini"
      case "google":
        return "gemini-1.5-flash"
      case "anthropic":
        return "claude-3-5-sonnet-20241022"
      default:
        return "Optional: override default model"
    }
  }

  return (
    <Card.Root mb={8} variant="outline">
      <Card.Header>
        <Heading size="sm">Add New Credential</Heading>
      </Card.Header>
      <Card.Body>
        <Box as="form" onSubmit={handleSubmit(onSubmit)}>
          <VStack gap={4} align="stretch">
            <Field
              label="Provider"
              required
              invalid={!!errors.provider_name}
              errorText={errors.provider_name?.message}
            >
              <SelectRoot
                collection={providers}
                size="md"
                onValueChange={(e: any) => {
                  setValue("provider_name", e.value[0])
                  setValidationResult(null)
                }}
              >
                <SelectTrigger>
                  <SelectValueText placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  {providers.items.map((provider) => (
                    <SelectItem key={provider.value} item={provider}>
                      {provider.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </SelectRoot>
            </Field>

            <Field
              label="API Key"
              required
              invalid={!!errors.api_key_encrypted}
              errorText={errors.api_key_encrypted?.message}
            >
              <InputGroup
                startElement={<FiKey />}
                endElement={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowApiKey(!showApiKey)}
                    type="button"
                  >
                    {showApiKey ? <FiEyeOff /> : <FiEye />}
                  </Button>
                }
              >
                <Input
                  {...register("api_key_encrypted", {
                    required: "API key is required",
                    minLength: {
                      value: 10,
                      message: "API key seems too short",
                    },
                  })}
                  type={showApiKey ? "text" : "password"}
                  placeholder="sk-..."
                  autoComplete="off"
                  onChange={() => setValidationResult(null)}
                />
              </InputGroup>
            </Field>

            <Field
              label="Model Name (Optional)"
              helperText={`Leave empty to use default: ${getPlaceholderModel(selectedProvider)}`}
            >
              <Input
                {...register("model_name")}
                type="text"
                placeholder={getPlaceholderModel(selectedProvider)}
              />
            </Field>

            <Checkbox
              {...register("is_default")}
              defaultChecked={false}
            >
              Set as default credential
            </Checkbox>

            {validationResult && (
              <Box
                p={3}
                borderRadius="md"
                bg={validationResult.valid ? "green.50" : "red.50"}
              >
                <HStack>
                  {validationResult.valid ? (
                    <FiCheck color="green" />
                  ) : (
                    <FiAlertCircle color="red" />
                  )}
                  <Text
                    fontSize="sm"
                    color={validationResult.valid ? "green.700" : "red.700"}
                  >
                    {validationResult.message || "Validation complete"}
                  </Text>
                </HStack>
              </Box>
            )}
          </VStack>

          <Flex mt={6} gap={3}>
            <Button
              variant="outline"
              onClick={validateCredential}
              loading={isValidating}
              disabled={!selectedProvider || !apiKey}
              type="button"
            >
              Test Connection
            </Button>
            <Button
              variant="solid"
              colorPalette="blue"
              type="submit"
              loading={isSubmitting}
            >
              Save
            </Button>
            <Button
              variant="ghost"
              onClick={onCancel}
              disabled={isSubmitting}
              type="button"
            >
              Cancel
            </Button>
          </Flex>
        </Box>
      </Card.Body>
    </Card.Root>
  )
}

export default LLMCredentialForm
