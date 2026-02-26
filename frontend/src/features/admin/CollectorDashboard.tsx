import { Box, Container, Heading, SimpleGrid, Text } from "@chakra-ui/react"
import { useState } from "react"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogHeader,
  DialogRoot,
} from "@/components/ui/dialog"
import { CollectorCard } from "./CollectorCard"
import { CollectorPluginForm } from "./CollectorForm"
import { useCollectors, useCreateAndEnable, usePluginCardData } from "./hooks"
import type { CollectorCardData } from "./types"

export const CollectorDashboard = () => {
  const { cards, isLoading } = usePluginCardData()
  const { plugins, toggleInstance, runCollector } = useCollectors()
  const createAndEnable = useCreateAndEnable()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedCard, setSelectedCard] = useState<
    CollectorCardData | undefined
  >(undefined)

  if (isLoading || plugins.isLoading) {
    return <Text>Loading collectors...</Text>
  }

  const handleToggle = (card: CollectorCardData) => {
    if (card.instance_id) {
      // Instance exists, toggle it
      toggleInstance.mutate({
        id: card.instance_id,
        is_active: !card.is_active,
      })
    } else {
      // No instance, create and enable
      const plugin = plugins.data?.find((p) => p.id === card.plugin_id)
      if (plugin) {
        createAndEnable.mutate(plugin)
      }
    }
  }

  const handleRun = (card: CollectorCardData) => {
    if (card.instance_id) {
      runCollector.mutate(card.instance_id)
    }
  }

  const handleEdit = (card: CollectorCardData) => {
    setSelectedCard(card)
    setIsDialogOpen(true)
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Heading size="lg" mb={8}>
        Data Collectors
      </Heading>

      {!cards || cards.length === 0 ? (
        <Box textAlign="center" py={10} bg="gray.50" borderRadius="md">
          <Text color="gray.500">No collector plugins registered.</Text>
        </Box>
      ) : (
        <>
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6}>
            {cards.map((card) => (
              <CollectorCard
                key={card.plugin_id}
                card={card}
                onEdit={() => handleEdit(card)}
                onToggle={() => handleToggle(card)}
                onRun={() => handleRun(card)}
              />
            ))}
          </SimpleGrid>

          <DialogRoot
            open={isDialogOpen}
            onOpenChange={(e) => {
              setIsDialogOpen(e.open)
              if (!e.open) setSelectedCard(undefined)
            }}
          >
            <DialogContent>
              <DialogHeader>
                {selectedCard?.instance_id
                  ? "Edit Collector"
                  : "Configure Collector"}
              </DialogHeader>
              <DialogCloseTrigger />
              <DialogBody>
                {selectedCard && (
                  <CollectorPluginForm
                    plugins={plugins.data || []}
                    initialValues={
                      selectedCard.instance_id
                        ? {
                            id: selectedCard.instance_id,
                            name: selectedCard.instance_name!,
                            plugin_id: selectedCard.plugin_id,
                            status: selectedCard.status,
                            config: selectedCard.config,
                            schedule_cron: selectedCard.schedule_cron,
                            last_run: selectedCard.last_run,
                            next_run: null,
                            is_active: selectedCard.is_active,
                            error_count: 0,
                            success_count: 0,
                          }
                        : undefined
                    }
                    onCancel={() => setIsDialogOpen(false)}
                    onSuccess={() => setIsDialogOpen(false)}
                  />
                )}
              </DialogBody>
            </DialogContent>
          </DialogRoot>
        </>
      )}
    </Container>
  )
}
