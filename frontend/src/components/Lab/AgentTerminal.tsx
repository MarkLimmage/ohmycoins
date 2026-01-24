import {
  Box,
  Button,
  Flex,
  HStack,
  Icon,
  Input,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useCallback, useEffect, useRef, useState } from "react"
import {
  FiArrowDown,
  FiCopy,
  FiDownload,
  FiSearch,
  FiX,
  FiXCircle,
} from "react-icons/fi"
import useCustomToast from "@/hooks/useCustomToast"
import AgentMessage from "./AgentMessage"
import type {
  AgentMessage as AgentMessageType,
  AgentTerminalProps,
} from "./types"

const AgentTerminal = ({
  sessionId,
  streamUrl,
  allowInteraction,
  onExport,
  onCancel,
}: AgentTerminalProps) => {
  const [messages, setMessages] = useState<AgentMessageType[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [showSearch, setShowSearch] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [showJumpToLatest, setShowJumpToLatest] = useState(false)
  const [filteredMessages, setFilteredMessages] = useState<AgentMessageType[]>(
    [],
  )

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const autoScrollRef = useRef(true)

  const { showSuccessToast, showErrorToast } = useCustomToast()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    autoScrollRef.current = true
    setShowJumpToLatest(false)
  }, [])

  useEffect(() => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      setFilteredMessages(
        messages.filter(
          (msg) =>
            msg.content.toLowerCase().includes(query) ||
            msg.type.toLowerCase().includes(query) ||
            msg.metadata?.tool_name?.toLowerCase().includes(query),
        ),
      )
    } else {
      setFilteredMessages(messages)
    }
  }, [searchQuery, messages])

  useEffect(() => {
    const ws = new WebSocket(streamUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      ws.send(JSON.stringify({ action: "subscribe", sessionId }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const newMessage: AgentMessageType = {
          id: data.id || `${Date.now()}-${Math.random()}`,
          type: data.type || "output",
          content: data.content || "",
          timestamp: data.timestamp || new Date().toISOString(),
          metadata: data.metadata,
        }

        setMessages((prev) => [...prev, newMessage])

        if (autoScrollRef.current) {
          setTimeout(() => scrollToBottom(), 100)
        }
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error)
      }
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      showErrorToast("Failed to connect to agent stream")
      setIsConnected(false)
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [streamUrl, sessionId, scrollToBottom, showErrorToast])

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight

    if (distanceFromBottom > 100) {
      autoScrollRef.current = false
      setShowJumpToLatest(true)
    } else {
      autoScrollRef.current = true
      setShowJumpToLatest(false)
    }
  }, [])

  const handleCopyTranscript = useCallback(async () => {
    const transcript = messages
      .map(
        (msg) =>
          `[${new Date(msg.timestamp).toLocaleTimeString()}] ${msg.type.toUpperCase()}: ${msg.content}`,
      )
      .join("\n\n")

    try {
      await navigator.clipboard.writeText(transcript)
      showSuccessToast("Transcript copied to clipboard")
    } catch (_error) {
      showErrorToast("Could not copy transcript to clipboard")
    }
  }, [messages, showSuccessToast, showErrorToast])

  const handleExport = useCallback(() => {
    if (onExport) {
      onExport()
      return
    }

    const transcript = messages
      .map(
        (msg) =>
          `[${new Date(msg.timestamp).toLocaleTimeString()}] ${msg.type.toUpperCase()}: ${msg.content}${
            msg.metadata?.tool_name ? `\nTool: ${msg.metadata.tool_name}` : ""
          }${
            msg.metadata?.execution_time
              ? ` (${msg.metadata.execution_time}ms)`
              : ""
          }`,
      )
      .join("\n\n")

    const blob = new Blob([transcript], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `agent-session-${sessionId}-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    showSuccessToast("Transcript exported successfully")
  }, [messages, sessionId, onExport, showSuccessToast])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "f") {
        e.preventDefault()
        setShowSearch(true)
        setTimeout(() => searchInputRef.current?.focus(), 100)
      }

      if ((e.ctrlKey || e.metaKey) && e.key === "c" && !showSearch) {
        e.preventDefault()
        handleCopyTranscript()
      }

      if (e.key === "Escape") {
        setShowSearch(false)
        setSearchQuery("")
      }
    },
    [showSearch, handleCopyTranscript],
  )

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    if (messages.length > 0 && autoScrollRef.current) {
      scrollToBottom()
    }
  }, [messages, scrollToBottom])

  const displayMessages = searchQuery ? filteredMessages : messages

  return (
    <Flex
      direction="column"
      h="100%"
      bg="gray.900"
      borderRadius="lg"
      overflow="hidden"
      border="1px solid"
      borderColor="whiteAlpha.300"
      role="region"
      aria-label="Agent Terminal"
    >
      {/* Header */}
      <HStack
        bg="gray.800"
        px={4}
        py={3}
        borderBottom="1px solid"
        borderColor="whiteAlpha.300"
        justify="space-between"
      >
        <HStack gap={3}>
          <HStack gap={2}>
            <Box
              w={2}
              h={2}
              borderRadius="full"
              bg={isConnected ? "green.400" : "red.400"}
              aria-label={isConnected ? "Connected" : "Disconnected"}
            />
            <Text fontSize="sm" fontWeight="semibold" color="gray.200">
              Session: {sessionId.slice(0, 8)}...
            </Text>
          </HStack>

          {isConnected && (
            <HStack gap={1}>
              <Spinner size="xs" color="gray.400" />
              <Text fontSize="xs" color="gray.400">
                Streaming
              </Text>
            </HStack>
          )}
        </HStack>

        <HStack gap={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setShowSearch(!showSearch)
              if (!showSearch) {
                setTimeout(() => searchInputRef.current?.focus(), 100)
              }
            }}
            aria-label="Search transcript"
            title="Search (Ctrl/Cmd+F)"
          >
            <Icon fontSize="md">
              <FiSearch />
            </Icon>
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={handleCopyTranscript}
            aria-label="Copy transcript"
            title="Copy transcript (Ctrl/Cmd+C)"
          >
            <Icon fontSize="md">
              <FiCopy />
            </Icon>
          </Button>

          <Button
            size="sm"
            variant="ghost"
            onClick={handleExport}
            aria-label="Export transcript"
            title="Export transcript"
          >
            <Icon fontSize="md">
              <FiDownload />
            </Icon>
          </Button>

          {onCancel && allowInteraction && (
            <Button
              size="sm"
              colorPalette="red"
              onClick={onCancel}
              aria-label="Cancel session"
            >
              <Icon fontSize="md">
                <FiXCircle />
              </Icon>
              <Text ml={1}>Cancel</Text>
            </Button>
          )}
        </HStack>
      </HStack>

      {/* Search Bar */}
      {showSearch && (
        <HStack
          bg="gray.800"
          px={4}
          py={2}
          borderBottom="1px solid"
          borderColor="whiteAlpha.300"
          gap={2}
        >
          <Icon fontSize="sm" color="gray.400">
            <FiSearch />
          </Icon>
          <Input
            ref={searchInputRef}
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="sm"
            variant="subtle"
            bg="gray.700"
            borderColor="whiteAlpha.300"
            _focus={{
              borderColor: "blue.400",
              outline: "2px solid",
              outlineColor: "blue.400",
            }}
            aria-label="Search messages"
          />
          <Text fontSize="xs" color="gray.400" whiteSpace="nowrap">
            {displayMessages.length} of {messages.length}
          </Text>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setShowSearch(false)
              setSearchQuery("")
            }}
            aria-label="Close search"
          >
            <Icon fontSize="sm">
              <FiX />
            </Icon>
          </Button>
        </HStack>
      )}

      {/* Messages Container */}
      <Box
        ref={containerRef}
        flex={1}
        overflowY="auto"
        overflowX="hidden"
        onScroll={handleScroll}
        css={{
          scrollBehavior: "smooth",
          "&::-webkit-scrollbar": {
            width: "8px",
          },
          "&::-webkit-scrollbar-track": {
            background: "rgba(0, 0, 0, 0.2)",
          },
          "&::-webkit-scrollbar-thumb": {
            background: "rgba(255, 255, 255, 0.2)",
            borderRadius: "4px",
          },
          "&::-webkit-scrollbar-thumb:hover": {
            background: "rgba(255, 255, 255, 0.3)",
          },
        }}
      >
        <VStack
          align="stretch"
          gap={0}
          role="log"
          aria-live="polite"
          aria-atomic="false"
          aria-relevant="additions"
        >
          {displayMessages.length === 0 ? (
            <Flex
              h="100%"
              align="center"
              justify="center"
              color="gray.500"
              py={8}
            >
              <Text fontSize="sm">
                {messages.length === 0
                  ? "Waiting for messages..."
                  : "No messages match your search"}
              </Text>
            </Flex>
          ) : (
            displayMessages.map((message) => (
              <AgentMessage key={message.id} message={message} />
            ))
          )}
          <div ref={messagesEndRef} />
        </VStack>
      </Box>

      {/* Jump to Latest Button */}
      {showJumpToLatest && (
        <Box position="absolute" bottom={4} right={4} zIndex={10}>
          <Button
            size="sm"
            colorPalette="blue"
            onClick={scrollToBottom}
            shadow="lg"
            aria-label="Jump to latest message"
          >
            <Icon fontSize="md">
              <FiArrowDown />
            </Icon>
            <Text ml={1}>Jump to Latest</Text>
          </Button>
        </Box>
      )}
    </Flex>
  )
}

export default AgentTerminal
