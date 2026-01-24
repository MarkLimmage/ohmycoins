import { Box } from "@chakra-ui/react"
import type { Meta, StoryObj } from "@storybook/react"
import { SafetyButton } from "./SafetyButton"

const meta: Meta<typeof SafetyButton> = {
  title: "Components/Floor/SafetyButton",
  component: SafetyButton,
  tags: ["autodocs"],
  argTypes: {
    action: { control: "text" },
    isDisabled: { control: "boolean" },
    cooldownSeconds: { control: "number" },
    requireConfirmation: { control: "boolean" },
    confirmationText: { control: "text" },
    buttonSize: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    colorScheme: {
      control: "select",
      options: ["red", "orange", "yellow"],
    },
  },
}

export default meta
type Story = StoryObj<typeof SafetyButton>

export const KillSwitch: Story = {
  args: {
    label: "EMERGENCY STOP",
    action: "KILL_SWITCH",
    description: "Immediately stops all trading bots and cancels open orders.",
    requireConfirmation: true,
    confirmationText: "STOP",
    cooldownSeconds: 10,
    colorScheme: "red",
    buttonSize: "lg",
    onConfirm: () => alert("KILL SWITCH ACTIVATED"),
  },
  render: (args) => (
    <Box p={8} bg="gray.100">
      <SafetyButton {...args} />
    </Box>
  ),
}

export const ConfirmTrade: Story = {
  args: {
    label: "Execute Trade",
    action: "EXECUTE_TRADE",
    description: "Buy 1.5 BTC at market price?",
    requireConfirmation: true,
    cooldownSeconds: 2,
    colorScheme: "orange",
    onConfirm: () => alert("Trade Executed"),
  },
}

export const SimpleAction: Story = {
  args: {
    label: "Clear Cache",
    action: "CLEAR_CACHE",
    requireConfirmation: false,
    colorScheme: "yellow",
    onConfirm: () => alert("Cache Cleared"),
  },
}
