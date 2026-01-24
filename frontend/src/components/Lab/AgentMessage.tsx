import { Box, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { format } from "date-fns"
import {
  FiAlertCircle,
  FiCheckCircle,
  FiCode,
  FiMessageSquare,
  FiTool,
} from "react-icons/fi"
import type { AgentMessage as AgentMessageType } from "./types"

const messageTypeConfig = {
  thought: {
    color: "#6b7280",
    icon: FiMessageSquare,
    fontStyle: "italic",
  },
  tool: {
    color: "#3b82f6",
    icon: FiTool,
  },
  result: {
    successColor: "#22c55e",
    errorColor: "#ef4444",
    successIcon: FiCheckCircle,
    errorIcon: FiAlertCircle,
  },
  input_request: {
    color: "#f59e0b",
    icon: FiCode,
  },
  output: {
    color: "inherit",
    bgColor: "rgba(59, 130, 246, 0.1)",
    fontWeight: "bold",
  },
}

interface AgentMessageProps {
  message: AgentMessageType
}

const AgentMessage = ({ message }: AgentMessageProps) => {
  const { type, content, timestamp, metadata } = message

  const getMessageStyle = () => {
    switch (type) {
      case "thought":
        return {
          color: messageTypeConfig.thought.color,
          fontStyle: messageTypeConfig.thought.fontStyle,
        }
      case "tool":
        return {
          color: messageTypeConfig.tool.color,
        }
      case "result":
        return {
          color: metadata?.error
            ? messageTypeConfig.result.errorColor
            : messageTypeConfig.result.successColor,
        }
      case "input_request":
        return {
          color: messageTypeConfig.input_request.color,
        }
      case "output":
        return {
          fontWeight: messageTypeConfig.output.fontWeight,
          bgColor: messageTypeConfig.output.bgColor,
          px: 2,
          py: 1,
          borderRadius: "md",
        }
      default:
        return {}
    }
  }

  const getIcon = () => {
    switch (type) {
      case "thought":
        return messageTypeConfig.thought.icon
      case "tool":
        return messageTypeConfig.tool.icon
      case "result":
        return metadata?.error
          ? messageTypeConfig.result.errorIcon
          : messageTypeConfig.result.successIcon
      case "input_request":
        return messageTypeConfig.input_request.icon
      default:
        return null
    }
  }

  const MessageIcon = getIcon()
  const messageStyle = getMessageStyle()
  const formattedTime = format(new Date(timestamp), "HH:mm:ss.SSS")

  const renderContent = () => {
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    const parts = content.split(codeBlockRegex)

    if (parts.length === 1) {
      return (
        <Text
          fontFamily="monospace"
          fontSize="sm"
          whiteSpace="pre-wrap"
          wordBreak="break-word"
          {...messageStyle}
        >
          {content}
        </Text>
      )
    }

    const renderPart = (part: string, index: number) => {
      if (index % 3 === 0) {
        return part ? (
          <Text
            key={`text-${index}`}
            fontFamily="monospace"
            fontSize="sm"
            whiteSpace="pre-wrap"
            wordBreak="break-word"
            {...messageStyle}
          >
            {part}
          </Text>
        ) : null
      }
      if (index % 3 === 1) {
        const language = part
        const code = parts[index + 1]
        return (
          <Box
            key={`code-${index}`}
            bg="rgba(0, 0, 0, 0.3)"
            p={2}
            borderRadius="md"
            my={1}
          >
            {language && (
              <Text fontSize="xs" color="gray.400" mb={1}>
                {language}
              </Text>
            )}
            <Text
              fontFamily="monospace"
              fontSize="sm"
              whiteSpace="pre"
              overflowX="auto"
              color="green.300"
            >
              {code}
            </Text>
          </Box>
        )
      }
      return null
    }

    return <Box>{parts.map((part, index) => renderPart(part, index))}</Box>
  }

  return (
    <Box
      role="log"
      aria-label={`${type} message`}
      py={2}
      px={3}
      borderBottom="1px solid"
      borderColor="whiteAlpha.200"
      _hover={{ bg: "whiteAlpha.50" }}
    >
      <VStack align="stretch" gap={1}>
        <HStack gap={2} alignItems="flex-start">
          <HStack gap={1} flexShrink={0} minW="90px">
            <Text fontSize="xs" color="gray.500" fontFamily="monospace">
              {formattedTime}
            </Text>
          </HStack>

          <HStack gap={1} flexShrink={0}>
            {MessageIcon && (
              <Icon fontSize="sm" color={messageStyle.color}>
                <MessageIcon />
              </Icon>
            )}
            <Text
              fontSize="xs"
              fontWeight="semibold"
              textTransform="uppercase"
              color="gray.400"
              minW="80px"
            >
              {type.replace("_", " ")}
            </Text>
          </HStack>

          <Box flex={1}>{renderContent()}</Box>
        </HStack>

        {metadata?.tool_name && (
          <Text fontSize="xs" color="gray.500" pl="90px">
            Tool: {metadata.tool_name}
            {metadata.execution_time !== undefined &&
              ` (${metadata.execution_time}ms)`}
          </Text>
        )}

        {metadata?.error && type !== "result" && (
          <Text fontSize="xs" color="red.400" pl="90px" fontStyle="italic">
            Error: {metadata.error}
          </Text>
        )}
      </VStack>
    </Box>
  )
}

export default AgentMessage
