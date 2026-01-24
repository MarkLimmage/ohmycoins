/**
 * Example usage of AgentTerminal component
 *
 * This file demonstrates how to integrate the AgentTerminal component
 * into your application for real-time agent monitoring.
 */

import { Box } from "@chakra-ui/react"
import { AgentTerminal } from "@/components/Lab"

// Example 1: Basic usage with WebSocket URL
export function BasicAgentTerminalExample() {
  return (
    <Box h="600px" p={4}>
      <AgentTerminal
        sessionId="example-session-123"
        streamUrl="wss://api.example.com/agent/stream"
        allowInteraction={true}
      />
    </Box>
  )
}

// Example 2: With custom export handler
export function AgentTerminalWithCustomExport() {
  const handleExport = () => {
    console.log("Custom export logic here")
    // e.g., send to server, save to IndexedDB, etc.
  }

  return (
    <Box h="600px" p={4}>
      <AgentTerminal
        sessionId="example-session-456"
        streamUrl="wss://api.example.com/agent/stream"
        allowInteraction={true}
        onExport={handleExport}
      />
    </Box>
  )
}

// Example 3: With cancel handler
export function AgentTerminalWithCancel() {
  const handleCancel = () => {
    console.log("Canceling agent execution...")
    // API call to cancel agent session
  }

  return (
    <Box h="600px" p={4}>
      <AgentTerminal
        sessionId="example-session-789"
        streamUrl="wss://api.example.com/agent/stream"
        allowInteraction={true}
        onCancel={handleCancel}
      />
    </Box>
  )
}

// Example 4: Read-only mode (no cancel button)
export function AgentTerminalReadOnly() {
  return (
    <Box h="600px" p={4}>
      <AgentTerminal
        sessionId="example-session-completed"
        streamUrl="wss://api.example.com/agent/stream"
        allowInteraction={false}
      />
    </Box>
  )
}

// Mock WebSocket server for testing
// In a real application, this would be handled by your backend
export function createMockWebSocketServer() {
  // This is just documentation - actual implementation would be in backend
  const mockMessages = [
    {
      id: "1",
      type: "thought",
      content: "Analyzing the user's request...",
      timestamp: new Date().toISOString(),
    },
    {
      id: "2",
      type: "tool",
      content: "Searching for relevant files in the codebase",
      timestamp: new Date().toISOString(),
      metadata: {
        tool_name: "search_files",
        execution_time: 123,
      },
    },
    {
      id: "3",
      type: "result",
      content:
        "Found 3 files matching the search criteria:\n- AgentTerminal.tsx\n- AgentMessage.tsx\n- types.ts",
      timestamp: new Date().toISOString(),
      metadata: {
        tool_name: "search_files",
        execution_time: 123,
      },
    },
    {
      id: "4",
      type: "tool",
      content: "Reading file contents",
      timestamp: new Date().toISOString(),
      metadata: {
        tool_name: "read_file",
      },
    },
    {
      id: "5",
      type: "result",
      content:
        "```typescript\nexport interface AgentTerminalProps {\n  sessionId: string\n  streamUrl: string\n}\n```",
      timestamp: new Date().toISOString(),
      metadata: {
        tool_name: "read_file",
        execution_time: 45,
      },
    },
    {
      id: "6",
      type: "thought",
      content: "I now have all the information needed to answer the question.",
      timestamp: new Date().toISOString(),
    },
    {
      id: "7",
      type: "output",
      content:
        "The AgentTerminal component is a streaming console for agent logs with full accessibility support. It features WebSocket streaming, search functionality, and export capabilities.",
      timestamp: new Date().toISOString(),
    },
  ]

  return {
    mockMessages,
    description:
      "Send these messages through WebSocket one by one to simulate agent execution",
  }
}

// Example WebSocket message format
export const exampleWebSocketMessage = {
  id: "msg-123",
  type: "tool", // 'thought' | 'tool' | 'result' | 'input_request' | 'output'
  content: "Executing search query...",
  timestamp: "2024-01-24T10:30:45.123Z",
  metadata: {
    tool_name: "search_files",
    execution_time: 245,
    // error: "Optional error message" // only for result type
  },
}
