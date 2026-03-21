import { Badge, Box, Button, Flex, IconButton, Text } from "@chakra-ui/react"
import { useState } from "react"
import { FiList, FiPlus } from "react-icons/fi"
import type { AgentSessionPublic } from "@/client"
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerRoot,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer"
import { SessionCreateForm } from "./SessionCreateForm"
import { SessionList } from "./SessionList"

interface SessionDrawerProps {
  sessions: AgentSessionPublic[]
  selectedId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function SessionDrawer({
  sessions,
  selectedId,
  onSelect,
  onDelete,
  open,
  onOpenChange,
}: SessionDrawerProps) {
  const [showCreateForm, setShowCreateForm] = useState(false)

  const activeCount = sessions.filter(
    (s) => s.status === "running" || s.status === "pending",
  ).length

  return (
    <>
      <DrawerRoot
        placement="start"
        open={open}
        onOpenChange={(e) => onOpenChange(e.open)}
        size="sm"
      >
        <DrawerBackdrop />
        <DrawerTrigger asChild>
          <Box position="relative" display="inline-block">
            <IconButton aria-label="Open sessions" variant="outline" size="sm">
              <FiList />
            </IconButton>
            {activeCount > 0 && (
              <Badge
                colorPalette="blue"
                position="absolute"
                top="-1"
                right="-1"
                fontSize="2xs"
                borderRadius="full"
                minW="4"
                textAlign="center"
              >
                {activeCount}
              </Badge>
            )}
          </Box>
        </DrawerTrigger>
        <DrawerContent>
          <DrawerCloseTrigger />
          <DrawerHeader>
            <Flex justify="space-between" align="center" w="full" pr={8}>
              <DrawerTitle>Sessions</DrawerTitle>
              <Button
                colorPalette="blue"
                size="xs"
                onClick={() => setShowCreateForm(true)}
              >
                <FiPlus />
                <Text ml={1}>New Session</Text>
              </Button>
            </Flex>
          </DrawerHeader>
          <DrawerBody>
            <SessionList
              sessions={sessions}
              selectedId={selectedId}
              onSelect={(id) => {
                onSelect(id)
                onOpenChange(false)
              }}
              onDelete={onDelete}
            />
          </DrawerBody>
        </DrawerContent>
      </DrawerRoot>

      <SessionCreateForm
        isOpen={showCreateForm}
        onClose={() => setShowCreateForm(false)}
        onCreated={(id) => {
          onSelect(id)
          setShowCreateForm(false)
          onOpenChange(false)
        }}
      />
    </>
  )
}
