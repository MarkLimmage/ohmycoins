import type { Meta, StoryObj } from '@storybook/react';
import { EquityCurve } from './EquityCurve';

const meta: Meta<typeof EquityCurve> = {
  title: 'Performance/EquityCurve',
  component: EquityCurve,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof EquityCurve>;

const mockData = [
  { date: 'Jan', equity: 1000 },
  { date: 'Feb', equity: 1200 },
  { date: 'Mar', equity: 1100 },
  { date: 'Apr', equity: 1400 },
  { date: 'May', equity: 1300 },
  { date: 'Jun', equity: 1500 },
];

export const Default: Story = {
  args: {
    data: mockData,
  },
};
