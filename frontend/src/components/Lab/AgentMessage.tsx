import { Box, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { useColorModeValue } from "@/components/ui/color-mode"
import { format } from "date-fns"
import {
  FiAlertCircle,
  FiCheckCircle,
  FiCode,
  FiMessageSquare,
  FiTool,
} from "react-icons/fi"
import type { AgentMessage as AgentMessageType } from "./types"

interface AgentMessageProps {
  message: AgentMessageType
}

const AgentMessage = ({ message }: AgentMessageProps) => {
  const { type, content, timestamp, metadata } = message

  // Hooks for adaptive colors
  const thoughtColor = useColorModeValue("gray.500", "gray.400")
  const toolColor = useColorModeValue("blue.600", "blue.400")
  const successColor = useColorModeValue("green.600", "green.400")
  const errorColor = useColorModeValue("red.600", "red.400")
  const inputColor = useColorModeValue("yellow.600", "yellow.400")
  const outputBg = useColorModeValue("blue.50", "whiteAlpha.200")
  const codeBg = useColorModeValue("gray.100", "whiteAlpha.200")
  const codeLangColor = useColorModeValue("gray.500", "gray.400")

  const getMessageStyle = () => {
    switch (type) {
      case "thought":
        return {
          color: thoughtColor,
          fontStyle: "italic",
        }
      case "tool":
        return {
          color: toolColor,
        }
      case "result":
        return {
          color: metadata?.error ? errorColor : successColor,
        }
      case "input_request":
        return {
          color: inputColor,
        }
      case "output":
        return {
          fontWeight: "bold",
          bg: outputBg,
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
        return FiMessageSquare
      case "tool":
        return FiTool
      case "result":
        return metadata?.error ? FiAlertCircle : FiCheckCircle
      case "input_request":
        return FiCode
      default:
        return null
    }
  }

  const MessageIcon = getIcon()
  const messageStyle = getMessageStyle()
  const formattedTime = format(new Date(timestamp), "HH:mm:ss.SSS")

  const renderContent = () => {
    // Regex to split code blocks: capturing both language and code content
    // Note: This regex assumes well-formed markdown code blocks
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
    
    // When split by regex with capturing groups, the array looks like:
    // [text_before, language, code, text_after, ...]
    const elements = []
    let i = 0
    while (i < parts.length) {
      // 1. Text part
      const textPart = parts[i]
      if (textPart) {
        elements.push(
          <Text
            key={`text-${i}`}
            fontFamily="monospace"
            fontSize="sm"
            whiteSpace="pre-wrap"
            wordBreak="break-word"
            {...messageStyle}
          >
            {textPart}
          </Text>
        )
      }
      i++
      
      // Check if we have a match (language and code)
      if (i < parts.length) {
        const language = parts[i]
        const code = parts[i + 1]
        
        if (code !== undefined) {
             elements.push(
              <Box
                key={`code-${i}`}
                bg={codeBg}
                p={2}
                borderRadius="md"
                my={1}
                overflowX="auto"
              >
                {language && (
                  <Text fontSize="xs" color={codeLangColor} mb={1} textTransform="lowercase">
                    {language}
                  </Text>
                )}
                <Text
                  fontFamily="monospace"
                  fontSize="xs"
                  whiteSpace="pre"
                >
                  {code}
                </Text>
              </Box>
            )
        }
        // Advance past language and code
        i += 2
      }
    }
    return elements
  }

  const borderColor = useColorModeValue("gray.200", "whiteAlpha.200")
  const hoverBg = useColorModeValue("gray.50", "whiteAlpha.50")

  return (
    <Box
      role="log"
      aria-label={`${type} message`}
      py={2}
      px={3}
      borderBottom="1px solid"
      borderColor={borderColor}
      _hover={{ bg: hoverBg }}
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
