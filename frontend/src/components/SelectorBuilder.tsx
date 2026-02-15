
import {
  Button,
  Input,
  VStack,
  HStack,
  Text,
  Box,
  Code
} from "@chakra-ui/react"
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogCloseTrigger,
  DialogBody,
  DialogFooter,
} from "./ui/dialog"
import { Field } from "./ui/field"
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
    <DialogRoot open={isOpen} onOpenChange={(e) => !e.open && onClose()} size="xl">
      <DialogContent>
        <DialogHeader>CSS Selector Builder</DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <VStack gap={4} align="stretch">
            <Text fontSize="sm" color="gray.500">
              Enter the target URL and the CSS selector you want to scrape.
            </Text>

            
            <Field label="Target URL">
              <Input 
                value={url} 
                onChange={(e) => setUrl(e.target.value)} 
                placeholder="https://example.com/price"
              />
            </Field>

            <Field label="CSS Selector">
              <HStack>
                <Input 
                  value={selector} 
                  onChange={(e) => setSelector(e.target.value)} 
                  placeholder=".price-value span" 
                />
                <Button onClick={handleTest} loading={isLoading}>Test</Button>
              </HStack>
            </Field>

            {previewText && (
              <Box p={3} bg="gray.100" borderRadius="md">
                <Text fontWeight="bold" mb={1}>Preview:</Text>
                <Code w="full" p={2} bg="white">{previewText}</Code>
              </Box>
            )}
          </VStack>
        </DialogBody>

        <DialogFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
          <Button colorScheme="blue" onClick={handleSave} disabled={!selector}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}
