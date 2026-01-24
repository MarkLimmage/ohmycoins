import type { StorybookConfig } from '@storybook/react-vite';

/**
 * Storybook configuration for Oh My Coins component library
 * 
 * Features:
 * - Accessibility addon (@storybook/addon-a11y) for WCAG 2.1 AA audits
 * - Automatic JSDoc → Storybook docs generation
 * - Chromatic integration for visual regression testing (preparation)
 * - React + TypeScript + Vite support
 * 
 * @see /docs/ui/DESIGN_SYSTEM.md
 * @see /docs/DOCUMENTATION_STRATEGY.md (Tier 4: Auto-Generated Docs)
 */
const config: StorybookConfig = {
  stories: [
    "../src/**/*.mdx",
    "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  addons: [
    "@storybook/addon-a11y", // Accessibility testing (axe-core)
    "@storybook/addon-docs", // Auto-generate docs from JSDoc
    "@chromatic-com/storybook", // Visual regression testing
    "@storybook/addon-vitest", // Vitest integration
    "@storybook/addon-onboarding" // Onboarding guide
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {}
  },
  docs: {
    autodocs: "tag" // Generate docs for stories tagged with "autodocs"
  },
  staticDirs: ['../public'], // Serve static assets from public folder
  core: {
    disableTelemetry: true, // Disable telemetry for privacy
  }
};

export default config;