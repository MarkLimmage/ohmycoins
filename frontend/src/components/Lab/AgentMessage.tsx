import { Box, Button, HStack, Icon, Text, VStack } from "@chakra-ui/react"
import { useColorModeValue } from "@/components/ui/color-mode"
import { format } from "date-fns"
import { useState } from "react"
import {
  FiAlertCircle,
  FiCheckCircle,
  FiChevronDown,
  FiChevronRight,
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
  const [isExpanded, setIsExpanded] = useState(false)

  // Hooks for adaptive colors
  const thoughtColor = useColorModeValue("gray.500", "gray.400")
  const toolColor = useColorModeValue("blue.600", "blue.400")
  const successColor = useColorModeValue("green.600", "green.400")
  const errorColor = useColorModeValue("red.600", "red.400")
  const inputColor = useColorModeValue("yellow.600", "yellow.400")
  const outputBg = useColorModeValue("blue.50", "whiteAlpha.200")
  const codeBg = useColorModeValue("gray.100", "whiteAlpha.200")
  const codeLangColor = useColorModeValue("gray.500", "gray.400")
  const metaColor = useColorModeValue("gray.600", "gray.300")
  const metaBg = useColorModeValue("gray.50", "whiteAlpha.100")
  const borderColor = useColorModeValue("gray.200", "whiteAlpha.200")
  const hoverBg = useColorModeValue("gray.50", "whiteAlpha.50")
  const chevronColor = useColorModeValue("gray.400", "gray.500")

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

  const hasDetails = metadata && Object.keys(metadata).length > 0 &&
    Object.keys(metadata).some(k => !["tool_name", "execution_time", "error"].includes(k) || (k === "raw" && metadata.raw))

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
    
    const elements = []
    let i = 0
    while (i < parts.length) {
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
        i += 2
      }
    }
    return elements
  }

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

          <Box flex={1}>
            {renderContent()}
            
            {hasDetails && isExpanded && (
              <Box
                mt={2}
                p={2}
                bg={metaBg}
                borderRadius="md"
                fontSize="xs"
                fontFamily="monospace"
                color={metaColor}
                border="1px solid"
                borderColor={borderColor}
                overflowX="auto"
              >
                <Text fontWeight="bold" mb={1} fontSize="10px" color="gray.500" textTransform="uppercase">Message Details</Text>
                <Text whiteSpace="pre-wrap" wordBreak="break-word">
                  {JSON.stringify(metadata, null, 2)}
                </Text>
              </Box>
            )}
          </Box>

          {hasDetails && (
            <Button
              size="xs"
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label={isExpanded ? "Collapse details" : "Expand details"}
              title={isExpanded ? "Collapse details" : "Expand details"}
              minW="auto"
              h="auto"
              p={1}
              color={chevronColor}
              _hover={{ color: "gray.700", bg: "blackAlpha.100" }}
            >
              <Icon fontSize="md">
                {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </Icon>
            </Button>
          )}
        </HStack>
      </VStack>
    </Box>
  )
}

export default AgentMessage
