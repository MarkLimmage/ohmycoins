import { Box, Button, HStack, Input } from "@chakra-ui/react"
import type React from "react"
import { useState } from "react"
import useCustomToast from "../../../hooks/useCustomToast"
import { useLabContext } from "../context/LabContext"

export const ChatInput = () => {
  const { state, dispatch } = useLabContext()
  const [message, setMessage] = useState("")
  const [isSending, setIsSending] = useState(false)
  const { showErrorToast } = useCustomToast()

  const handleSend = async () => {
    if (!message.trim() || !state.sessionId) return

    const sentText = message.trim()
    setIsSending(true)
    try {
      const token = localStorage.getItem("access_token")
      const response = await fetch(
        `/api/v1/lab/agent/sessions/${state.sessionId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content: sentText }),
        },
      )

      if (!response.ok) {
        throw new Error("Failed to send message")
      }

      const saved = await response.json()

      // Optimistic render: dispatch user_message so it appears in DialoguePanel immediately
      dispatch({
        type: "PROCESS_EVENT",
        payload: {
          event_type: "user_message",
          stage: saved.stage || "BUSINESS_UNDERSTANDING",
          sequence_id: saved.sequence_id,
          timestamp: saved.created_at || new Date().toISOString(),
          payload: { content: sentText },
        },
      })

      setMessage("")
    } catch (_error) {
      showErrorToast("Error sending message")
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isDisabled = !state.isConnected || isSending

  return (
    <Box p={4} borderTop="1px solid" borderColor="gray.200" bg="white">
      <HStack>
        <Input
          placeholder={isDisabled ? "Session not active" : "Type a message..."}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isDisabled}
          bg="gray.50"
        />
        <Button
          colorScheme="blue"
          onClick={handleSend}
          loading={isSending}
          disabled={isDisabled || !message.trim()}
        >
          Send
        </Button>
      </HStack>
    </Box>
  )
}
