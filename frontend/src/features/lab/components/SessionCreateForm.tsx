import { Button, HStack, Text, Textarea, VStack } from "@chakra-ui/react"
import { useState } from "react"
import {
  DialogBackdrop,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { useCreateSession, useLlmCredentials } from "../hooks"

interface SessionCreateFormProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (sessionId: string) => void
}

export function SessionCreateForm({
  isOpen,
  onClose,
  onCreated,
}: SessionCreateFormProps) {
  const [goal, setGoal] = useState("")
  const [selectedCredentialId, setSelectedCredentialId] = useState<string>("")
  const createSession = useCreateSession()
  const { data: credentials } = useLlmCredentials()

  const handleSubmit = () => {
    if (!goal.trim()) return

    createSession.mutate(
      {
        user_goal: goal.trim(),
        llm_credential_id: selectedCredentialId || undefined,
      },
      {
        onSuccess: (session) => {
          setGoal("")
          setSelectedCredentialId("")
          onCreated(session.id)
        },
      },
    )
  }

  const credentialsList = Array.isArray(credentials) ? credentials : []

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={(details) => {
        if (!details.open) onClose()
      }}
    >
      <DialogBackdrop />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Lab Session</DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <VStack align="stretch" gap={4}>
            <VStack align="stretch" gap={1}>
              <Text fontSize="sm" fontWeight="medium">
                Goal
              </Text>
              <Textarea
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Describe what you want the AI agents to analyze or build..."
                rows={4}
                autoFocus
              />
              <Text fontSize="xs" color="gray.500">
                Example: &quot;Analyze BTC sentiment from news data and identify
                bullish/bearish patterns over the last 7 days&quot;
              </Text>
            </VStack>

            {credentialsList.length > 0 && (
              <VStack align="stretch" gap={1}>
                <Text fontSize="sm" fontWeight="medium">
                  LLM Provider
                </Text>
                <select
                  value={selectedCredentialId}
                  onChange={(e) => setSelectedCredentialId(e.target.value)}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--chakra-colors-whiteAlpha-300)",
                    background: "var(--chakra-colors-gray-800)",
                    color: "inherit",
                    fontSize: "14px",
                  }}
                >
                  <option value="">System Default</option>
                  {credentialsList.map((cred) => (
                    <option key={cred.id} value={cred.id}>
                      {cred.provider}
                      {cred.model_name ? ` (${cred.model_name})` : ""}
                      {cred.is_default ? " - Default" : ""}
                    </option>
                  ))}
                </select>
              </VStack>
            )}
          </VStack>
        </DialogBody>
        <DialogFooter>
          <HStack gap={3}>
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              disabled={!goal.trim() || createSession.isPending}
              loading={createSession.isPending}
              loadingText="Creating..."
            >
              Start Session
            </Button>
          </HStack>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}
