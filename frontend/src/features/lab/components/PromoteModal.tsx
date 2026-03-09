import { Button, HStack, Textarea, VStack } from "@chakra-ui/react"
import { useState } from "react"
import {
  DialogBackdrop,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"

interface PromoteModalProps {
  isOpen: boolean
  onClose: () => void
  artifactName?: string
  onSubmit: (data: PromoteFormData) => void
}

export interface PromoteFormData {
  algorithm_name: string
  description: string
  position_limit: number
  daily_loss_limit: number
  execution_frequency: "1h" | "4h" | "12h" | "24h"
}

export function PromoteModal({
  isOpen,
  onClose,
  artifactName,
  onSubmit,
}: PromoteModalProps) {
  const [formData, setFormData] = useState<PromoteFormData>({
    algorithm_name: artifactName || "",
    description: "",
    position_limit: 100,
    daily_loss_limit: 5,
    execution_frequency: "4h",
  })

  const handleSubmit = () => {
    if (!formData.algorithm_name.trim() || !formData.description.trim()) {
      return
    }
    onSubmit(formData)
    // Reset form
    setFormData({
      algorithm_name: artifactName || "",
      description: "",
      position_limit: 100,
      daily_loss_limit: 5,
      execution_frequency: "4h",
    })
  }

  const isValid =
    formData.algorithm_name.trim().length > 0 &&
    formData.description.trim().length > 0 &&
    formData.position_limit > 0 &&
    formData.daily_loss_limit > 0

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={(details) => {
        if (!details.open) onClose()
      }}
    >
      <DialogBackdrop />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Promote Model to Floor</DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <VStack align="stretch" gap={4}>
            {/* Algorithm Name */}
            <VStack align="stretch" gap={2}>
              <label
                htmlFor="algorithm_name"
                style={{ fontSize: "14px", fontWeight: "500" }}
              >
                Algorithm Name
              </label>
              <input
                id="algorithm_name"
                type="text"
                placeholder="e.g., BTC Momentum Trader v1"
                value={formData.algorithm_name}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    algorithm_name: e.target.value,
                  })
                }
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--chakra-colors-whiteAlpha-300)",
                  background: "var(--chakra-colors-gray-800)",
                  color: "inherit",
                  fontSize: "14px",
                }}
              />
            </VStack>

            {/* Description */}
            <VStack align="stretch" gap={2}>
              <label
                htmlFor="description"
                style={{ fontSize: "14px", fontWeight: "500" }}
              >
                Description
              </label>
              <Textarea
                id="description"
                placeholder="Describe the strategy, target market, and key parameters..."
                value={formData.description}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    description: e.target.value,
                  })
                }
                rows={3}
              />
            </VStack>

            {/* Position Limit */}
            <VStack align="stretch" gap={2}>
              <label
                htmlFor="position_limit"
                style={{ fontSize: "14px", fontWeight: "500" }}
              >
                Position Limit (%)
              </label>
              <input
                id="position_limit"
                type="number"
                value={formData.position_limit}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    position_limit: parseFloat(e.target.value) || 0,
                  })
                }
                min={0}
                max={100}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--chakra-colors-whiteAlpha-300)",
                  background: "var(--chakra-colors-gray-800)",
                  color: "inherit",
                  fontSize: "14px",
                }}
              />
            </VStack>

            {/* Daily Loss Limit */}
            <VStack align="stretch" gap={2}>
              <label
                htmlFor="daily_loss_limit"
                style={{ fontSize: "14px", fontWeight: "500" }}
              >
                Daily Loss Limit (%)
              </label>
              <input
                id="daily_loss_limit"
                type="number"
                value={formData.daily_loss_limit}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    daily_loss_limit: parseFloat(e.target.value) || 0,
                  })
                }
                min={0}
                max={100}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--chakra-colors-whiteAlpha-300)",
                  background: "var(--chakra-colors-gray-800)",
                  color: "inherit",
                  fontSize: "14px",
                }}
              />
            </VStack>

            {/* Execution Frequency */}
            <VStack align="stretch" gap={2}>
              <label
                htmlFor="execution_frequency"
                style={{ fontSize: "14px", fontWeight: "500" }}
              >
                Execution Frequency
              </label>
              <select
                id="execution_frequency"
                value={formData.execution_frequency}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    execution_frequency: e.target.value as
                      | "1h"
                      | "4h"
                      | "12h"
                      | "24h",
                  })
                }
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: "1px solid var(--chakra-colors-whiteAlpha-300)",
                  background: "var(--chakra-colors-gray-800)",
                  color: "inherit",
                  fontSize: "14px",
                }}
              >
                <option value="1h">Every 1 Hour</option>
                <option value="4h">Every 4 Hours</option>
                <option value="12h">Every 12 Hours</option>
                <option value="24h">Every 24 Hours</option>
              </select>
            </VStack>
          </VStack>
        </DialogBody>
        <DialogFooter>
          <HStack gap={3}>
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              disabled={!isValid}
            >
              Promote to Floor
            </Button>
          </HStack>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}
