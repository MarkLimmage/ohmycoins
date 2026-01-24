/**
 * Custom Storybook theme matching Oh My Coins Design System
 *
 * Colors aligned with DESIGN_SYSTEM.md Section 4.3 Color Palette:
 * - Glass: #3b82f6 (blue-500)
 * - Human: #10b981 (green-500)
 * - Catalyst: #f59e0b (amber-500)
 * - Exchange: #8b5cf6 (purple-500)
 *
 * @see /docs/ui/DESIGN_SYSTEM.md
 */
export const theme = {
  base: "light" as const,

  // Brand
  brandTitle: "Oh My Coins Component Library",
  brandUrl: "https://github.com/ohmycoins",
  brandImage: undefined, // Add logo URL when available
  brandTarget: "_self" as const,

  // Typography
  fontBase:
    '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  fontCode: '"Fira Code", "Courier New", monospace',

  // Color palette matching DESIGN_SYSTEM.md
  colorPrimary: "#3b82f6", // Glass blue
  colorSecondary: "#10b981", // Human green

  // UI colors
  appBg: "#ffffff",
  appContentBg: "#f9fafb", // gray-50
  appPreviewBg: "#ffffff",
  appBorderColor: "#e5e7eb", // gray-200
  appBorderRadius: 8,

  // Text colors
  textColor: "#111827", // gray-900
  textInverseColor: "#ffffff",
  textMutedColor: "#6b7280", // gray-500

  // Toolbar colors
  barTextColor: "#6b7280",
  barSelectedColor: "#3b82f6", // Glass blue
  barHoverColor: "#10b981", // Human green
  barBg: "#ffffff",

  // Form colors
  inputBg: "#ffffff",
  inputBorder: "#d1d5db", // gray-300
  inputTextColor: "#111827",
  inputBorderRadius: 6,

  // Button colors
  buttonBg: "#3b82f6",
  buttonBorder: "#3b82f6",

  // Boolean colors (for accessibility addon results)
  booleanBg: "#e5e7eb",
  booleanSelectedBg: "#3b82f6",
}
