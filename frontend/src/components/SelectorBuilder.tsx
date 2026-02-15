
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  HStack,
  Text,
  Box,
  Code
} from "@chakra-ui/react"
import { useState } from "react"

interface SelectorBuilderProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (selector: string) => void
  initialUrl?: string
}

export function SelectorBuilder({ isOpen, onClose, onSelect, initialUrl = "" }: SelectorBuilderProps) {
  const [url, setUrl] = useState(initialUrl)
  const [selector, setSelector] = useState("")
  const [previewText, setPreviewText] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // In a real implementation, this would call a backend endpoint that
  // fetches the URL and tests the selector significantly.
  // For now, it's a "Builder" UI helper.
  const handleTest = async () => {
    setIsLoading(true)
    try {
        // Mock testing for UI demonstration
        await new Promise(r => setTimeout(r, 1000))
        setPreviewText(`Mock Result: Found "123.45" at ${selector}`)
    } catch (e) {
        setPreviewText("Error: Could not fetch URL")
    } finally {
        setIsLoading(false)
    }
  }

  const handleSave = () => {
    onSelect(selector)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>CSS Selector Builder</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Text fontSize="sm" color="gray.500">
              Enter the target URL and the CSS selector you want to scrape.
            </Text>
            
            <FormControl>
              <FormLabel>Target URL</FormLabel>
              <Input 
                value={url} 
                onChange={(e) => setUrl(e.target.value)} 
                placeholder="https://example.com/price"
              />
            </FormControl>

            <FormControl>
              <FormLabel>CSS Selector</FormLabel>
              <HStack>
                <Input 
                  value={selector} 
                  onChange={(e) => setSelector(e.target.value)} 
                  placeholder=".price-value span" 
                />
                <Button onClick={handleTest} isLoading={isLoading}>Test</Button>
              </HStack>
            </FormControl>

            {previewText && (
              <Box p={3} bg="gray.100" borderRadius="md">
                <Text fontWeight="bold" mb={1}>Preview:</Text>
                <Code w="full" p={2} bg="white">{previewText}</Code>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
          <Button colorScheme="blue" onClick={handleSave} isDisabled={!selector}>
            Use Selector
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}
