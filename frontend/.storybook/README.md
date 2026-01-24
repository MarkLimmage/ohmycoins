# Storybook Configuration

**Version**: 1.0  
**Date**: 2026-01-24  
**Storybook Version**: 10.2.0  
**Purpose**: Component library documentation and accessibility testing for Oh My Coins

---

## Overview

This directory contains Storybook configuration for the Oh My Coins frontend component library. Storybook provides:

1. **Component Documentation**: Auto-generated from JSDoc comments
2. **Accessibility Testing**: Automated WCAG 2.1 AA audits via axe-core
3. **Visual Testing**: Preparation for Chromatic visual regression testing
4. **Interactive Development**: Isolated component development environment

---

## Configuration Files

### `main.ts`
**Purpose**: Core Storybook configuration

**Key Settings**:
- **Stories Location**: `../src/**/*.stories.@(js|jsx|mjs|ts|tsx)`
  - All component stories live alongside their components
  - Example: `src/components/LedgerCard/LedgerCard.stories.tsx`

- **Addons**:
  - `@storybook/addon-a11y`: Accessibility testing (axe-core)
  - `@storybook/addon-docs`: Auto-generate docs from JSDoc
  - `@chromatic-com/storybook`: Visual regression testing
  - `@storybook/addon-vitest`: Vitest integration for testing
  - `@storybook/addon-onboarding`: Onboarding guide

- **Framework**: `@storybook/react-vite`
  - Optimized for Vite build tool
  - React 19 + TypeScript support

- **Autodocs**: Enabled (tag stories with `autodocs` to generate docs)

### `preview.ts`
**Purpose**: Global decorators, parameters, and theming

**Key Settings**:
- **Custom Theme**: Matches DESIGN_SYSTEM.md color palette
  - Glass: #3b82f6 (blue)
  - Human: #10b981 (green)
  - Catalyst: #f59e0b (amber)
  - Exchange: #8b5cf6 (purple)

- **Accessibility Configuration**:
  - WCAG 2.1 AA compliance checks
  - Color contrast validation
  - Keyboard navigation testing
  - Focus order semantics

- **Backgrounds**: Light, Dark, Glass blue (for contrast testing)

- **Viewports**: Mobile (375px), Tablet (768px), Desktop (1440px)

### `theme.ts`
**Purpose**: Custom Storybook theme

**Design Decisions**:
1. **Color Palette**: Directly aligned with DESIGN_SYSTEM.md Section 4.3
   - Primary: Glass blue (#3b82f6)
   - Secondary: Human green (#10b981)
   - All UI colors match Tailwind gray scale

2. **Typography**:
   - Font: Inter (matches application)
   - Code: Fira Code (monospace)
   - Sizes match DESIGN_SYSTEM.md Section 4.4

3. **Branding**:
   - Title: "Oh My Coins Component Library"
   - Light theme (matches application default)

---

## Usage

### Running Storybook Locally

```bash
# Start Storybook development server
npm run storybook

# Build static Storybook for deployment
npm run build-storybook
```

Storybook runs on: **http://localhost:6006**

### Writing Stories

Create a story file alongside your component:

```typescript
// src/components/LedgerCard/LedgerCard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { LedgerCard } from './LedgerCard';

/**
 * LedgerCard displays ledger data with charts and metrics.
 * 
 * ## Accessibility
 * - ARIA labels on all interactive elements
 * - Keyboard navigation: Tab, Enter, Esc
 * - Table view toggle: Ctrl+Shift+T
 * 
 * @component
 */
const meta: Meta<typeof LedgerCard> = {
  title: 'Components/Ledgers/LedgerCard',
  component: LedgerCard,
  tags: ['autodocs'], // Enable auto-generated docs
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof LedgerCard>;

/**
 * Glass Ledger Card showing TVL and fee metrics
 */
export const GlassLedger: Story = {
  args: {
    ledgerType: 'glass',
    data: {
      tvl: 1234567890,
      fees24h: 123456,
      change24h: 5.23,
    },
  },
};

/**
 * Loading state with skeleton screen
 */
export const Loading: Story = {
  args: {
    ledgerType: 'glass',
    isLoading: true,
  },
};
```

### Accessibility Testing Workflow

1. **Automatic Audits**: axe-core runs on every story
   - View results in "Accessibility" addon panel
   - All violations must be fixed before PR approval

2. **Keyboard Navigation**:
   - Tab through interactive elements
   - Verify focus indicators (2px outline, 3:1 contrast)
   - Test keyboard shortcuts (Ctrl+Shift+T for table view)

3. **Color Contrast**:
   - Use "Backgrounds" toolbar to test on different backgrounds
   - Verify 4.5:1 contrast ratio for normal text
   - Verify 3:1 contrast ratio for large text

4. **Screen Reader Testing** (Manual):
   - Use macOS VoiceOver or NVDA (Windows)
   - Verify ARIA labels are descriptive
   - Verify focus order is logical

---

## Performance Targets

Per SYSTEM_REQUIREMENTS.md NFR-P-005:

- **Build Time**: < 30 seconds
- **Story Render Time**: < 100ms
- **Hot Reload**: < 500ms

Monitor build times with:

```bash
time npm run build-storybook
```

---

## Chromatic Integration (Future)

**Status**: Configuration prepared, not yet deployed

**Purpose**: Visual regression testing to catch UI changes

**Workflow** (when enabled):
1. Push changes to branch
2. Chromatic captures screenshots of all stories
3. Review visual diffs in Chromatic dashboard
4. Approve or reject changes

**Configuration**:
- Addon already installed: `@chromatic-com/storybook`
- Requires Chromatic account and project token
- See: https://www.chromatic.com/docs/

---

## Troubleshooting

### Storybook won't start
```bash
# Clear cache and reinstall
rm -rf node_modules .storybook-cache
npm install
npm run storybook
```

### Accessibility addon not showing
- Verify `@storybook/addon-a11y` is in `main.ts` addons array
- Check browser console for errors
- Restart Storybook

### Theme not applying
- Verify `theme.ts` is imported in `preview.ts`
- Check `docs.theme` parameter is set
- Clear browser cache

### Build time > 30 seconds
- Check for large dependencies in stories
- Use code splitting for heavy components
- Consider lazy loading for non-critical stories

---

## Related Documentation

- [DESIGN_SYSTEM.md](/docs/ui/DESIGN_SYSTEM.md) - Component specifications
- [DOCUMENTATION_STRATEGY.md](/docs/DOCUMENTATION_STRATEGY.md) - Tier 4 auto-docs
- [frontend/README.md](/frontend/README.md) - Frontend development guide
- [Storybook Docs](https://storybook.js.org/docs/react/) - Official documentation

---

**Maintained By**: The Architect (Track C)  
**Last Updated**: 2026-01-24  
**Storybook URL**: http://localhost:6006 (development)
