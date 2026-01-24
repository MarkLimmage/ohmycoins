import type { Meta, StoryObj } from "@storybook/react"
import AgentTerminal from "./AgentTerminal"

const meta: Meta<typeof AgentTerminal> = {
  title: "Components/Lab/AgentTerminal",
  component: AgentTerminal,
  tags: ["autodocs"],
  argTypes: {
    allowInteraction: { control: "boolean" },
    onExport: { action: "exported" },
    onCancel: { action: "cancelled" },
  },
}

export default meta
type Story = StoryObj<typeof AgentTerminal>

export const Connected: Story = {
  args: {
    sessionId: "test-session-1",
    streamUrl: "wss://echo.websocket.org",
    allowInteraction: true,
  },
}

export const ReadOnly: Story = {
  args: {
    sessionId: "history-session-2",
    streamUrl: "",
    allowInteraction: false,
  },
}
