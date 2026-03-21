import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderWithProviders } from "@/test-utils"
import Sidebar from "./Sidebar"

// Mock router Link
vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    to,
    onClick,
  }: {
    children: React.ReactNode
    to: string
    onClick?: () => void
  }) => (
    <a href={to} onClick={onClick}>
      {children}
    </a>
  ),
}))

// Mock useAuth
vi.mock("@/hooks/useAuth", () => ({
  default: () => ({ logout: vi.fn() }),
}))

// Helper: in jsdom, Chakra responsive `display={{ base: "none", md: "flex" }}`
// hides the desktop sidebar. Use `hidden: true` to query those elements.
function getDesktopButton(name: string) {
  return screen.getByRole("button", { name, hidden: true })
}

describe("Sidebar", () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it("renders collapse toggle button", () => {
    renderWithProviders(<Sidebar />)
    expect(getDesktopButton("Collapse sidebar")).toBeInTheDocument()
  })

  it("starts expanded by default (no localStorage)", () => {
    renderWithProviders(<Sidebar />)
    expect(getDesktopButton("Collapse sidebar")).toBeInTheDocument()
  })

  it("starts collapsed when localStorage has sidebar-collapsed=true", () => {
    localStorage.setItem("sidebar-collapsed", "true")
    renderWithProviders(<Sidebar />)
    expect(getDesktopButton("Expand sidebar")).toBeInTheDocument()
  })

  it("toggles collapsed state and persists to localStorage", async () => {
    const user = userEvent.setup()
    renderWithProviders(<Sidebar />)

    expect(localStorage.getItem("sidebar-collapsed")).toBeNull()

    // Click to collapse
    await user.click(getDesktopButton("Collapse sidebar"))
    expect(localStorage.getItem("sidebar-collapsed")).toBe("true")
    expect(getDesktopButton("Expand sidebar")).toBeInTheDocument()

    // Click to expand again
    await user.click(getDesktopButton("Expand sidebar"))
    expect(localStorage.getItem("sidebar-collapsed")).toBe("false")
    expect(getDesktopButton("Collapse sidebar")).toBeInTheDocument()
  })
})
