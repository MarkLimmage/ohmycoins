import type { Meta, StoryObj } from "@storybook/react"
import { fn } from "@storybook/test"
import { KillSwitch } from "./KillSwitch"

const meta: Meta<typeof KillSwitch> = {
  component: KillSwitch,
  title: "Floor/KillSwitch",
  args: {
    onEmergencyStop: fn(),
  },
}
export default meta
type Story = StoryObj<typeof KillSwitch>

export const Active: Story = {
  args: {
    isActive: true,
  },
}

export const Inactive: Story = {
  args: {
    isActive: false,
  },
}
