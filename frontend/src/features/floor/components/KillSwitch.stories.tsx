import type { Meta, StoryObj } from "@storybook/react";
import { KillSwitch } from "./KillSwitch";
import { fn } from '@storybook/test';

const meta: Meta<typeof KillSwitch> = {
  component: KillSwitch,
  title: "Floor/KillSwitch",
  args: {
      onEmergencyStop: fn(),
  }
};
export default meta;
type Story = StoryObj<typeof KillSwitch>;

export const Active: Story = {
  args: {
    isActive: true,
  },
};

export const Inactive: Story = {
    args: {
      isActive: false,
    },
};
