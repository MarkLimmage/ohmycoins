import type { Meta, StoryObj } from '@storybook/react';

const Welcome = () => {
  return (
    <div style={{ padding: '2rem', fontFamily: 'Inter, sans-serif' }}>
      <h1 style={{ color: '#111827', marginBottom: '1rem' }}>
        Welcome to Oh My Coins Component Library
      </h1>
      
      <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
        Built with React, TypeScript, and Tailwind CSS. Tested for accessibility (WCAG 2.1 AA).
      </p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        <div style={{ padding: '1rem', backgroundColor: '#3b82f6', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>Glass</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>On-chain data</p>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#10b981', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>Human</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>Social sentiment</p>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#f59e0b', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>Catalyst</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>Events & alerts</p>
        </div>
        
        <div style={{ padding: '1rem', backgroundColor: '#8b5cf6', color: 'white', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 0.5rem 0' }}>Exchange</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>Trading data</p>
        </div>
      </div>
      
      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
        <h2 style={{ color: '#111827', marginBottom: '0.5rem' }}>Accessibility Features</h2>
        <ul style={{ color: '#6b7280', paddingLeft: '1.5rem' }}>
          <li>ARIA labels on all interactive elements</li>
          <li>Keyboard navigation support (Tab, Enter, Esc)</li>
          <li>4.5:1 color contrast ratio for text</li>
          <li>Focus indicators with 2px outline</li>
          <li>Table view toggle for data visualizations (Ctrl+Shift+T)</li>
        </ul>
      </div>
    </div>
  );
};

/**
 * Welcome to the Oh My Coins Component Library!
 * 
 * This Storybook instance provides:
 * - Interactive component documentation
 * - Automated accessibility testing (WCAG 2.1 AA)
 * - Visual regression testing preparation
 * 
 * ## Getting Started
 * 
 * 1. Browse components in the sidebar
 * 2. View accessibility results in the "Accessibility" tab
 * 3. Test components across different viewports and backgrounds
 * 
 * ## Color Palette
 * 
 * Our design system uses four primary colors representing the 4 Ledgers:
 * - **Glass** (#3b82f6): On-chain data, financial metrics
 * - **Human** (#10b981): Social sentiment, community activity
 * - **Catalyst** (#f59e0b): Events, alerts, breaking news
 * - **Exchange** (#8b5cf6): Trading data, prices, volumes
 */
const meta: Meta<typeof Welcome> = {
  title: 'Introduction/Welcome',
  component: Welcome,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof Welcome>;

/**
 * Welcome screen showing the color palette and accessibility features
 */
export const Default: Story = {};
