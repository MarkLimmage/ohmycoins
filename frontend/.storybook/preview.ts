import type { Preview } from '@storybook/react-vite';
import { theme } from './theme';

/**
 * Storybook preview configuration
 * 
 * Global decorators, parameters, and theming applied to all stories.
 * 
 * Features:
 * - Custom theme matching DESIGN_SYSTEM.md color palette
 * - Accessibility addon configured for WCAG 2.1 AA audits
 * - Dark mode support (preparation)
 * 
 * @see /docs/ui/DESIGN_SYSTEM.md (Section 4.3: Color Palette)
 */
const preview: Preview = {
  parameters: {
    // Apply custom theme
    docs: {
      theme: theme,
    },
    
    // Control matchers for automatic control type detection
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
      expanded: true, // Expand controls by default
    },
    
    // Accessibility addon configuration
    a11y: {
      // Run axe-core audits on all stories
      config: {
        rules: [
          {
            // WCAG 2.1 AA color contrast requirements
            id: 'color-contrast',
            enabled: true,
          },
          {
            // Keyboard navigation requirements
            id: 'focus-order-semantics',
            enabled: true,
          },
        ],
      },
      // Options for axe-core
      options: {
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
        },
      },
    },
    
    // Background color options for testing contrast
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#1f2937', // gray-800
        },
        {
          name: 'glass',
          value: '#3b82f6', // Glass blue
        },
      ],
    },
    
    // Viewport options for responsive testing
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
        tablet: {
          name: 'Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        desktop: {
          name: 'Desktop',
          styles: {
            width: '1440px',
            height: '900px',
          },
        },
      },
    },
  },
};

export default preview;