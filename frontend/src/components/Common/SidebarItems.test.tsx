import { screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { renderWithProviders } from "@/test-utils"
import SidebarItems from "./SidebarItems"

// Mock the router Link to render a plain anchor
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

describe("SidebarItems", () => {
  it("renders all menu items with text when expanded", () => {
    renderWithProviders(<SidebarItems collapsed={false} />)
    expect(screen.getByText("Menu")).toBeInTheDocument()
    expect(screen.getByText("Dashboard")).toBeInTheDocument()
    expect(screen.getByText("Collectors")).toBeInTheDocument()
    expect(screen.getByText("The Lab")).toBeInTheDocument()
    expect(screen.getByText("The Floor")).toBeInTheDocument()
  })

  it("hides text labels and Menu heading when collapsed", () => {
    renderWithProviders(<SidebarItems collapsed={true} />)
    expect(screen.queryByText("Menu")).not.toBeInTheDocument()
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument()
    expect(screen.queryByText("Collectors")).not.toBeInTheDocument()
    expect(screen.queryByText("The Lab")).not.toBeInTheDocument()
  })

  it("renders navigation links with correct paths", () => {
    renderWithProviders(<SidebarItems collapsed={false} />)
    const links = screen.getAllByRole("link")
    const hrefs = links.map((link) => link.getAttribute("href"))
    expect(hrefs).toContain("/")
    expect(hrefs).toContain("/collectors")
    expect(hrefs).toContain("/lab")
    expect(hrefs).toContain("/floor")
  })

  it("calls onClose when a link is clicked", async () => {
    const onClose = vi.fn()
    renderWithProviders(<SidebarItems onClose={onClose} collapsed={false} />)
    const dashboardLinks = screen.getAllByText("Dashboard")
    dashboardLinks[0].closest("a")!.click()
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("shows title tooltip attributes when collapsed", () => {
    const { container } = renderWithProviders(<SidebarItems collapsed={true} />)
    // Each navigation item should have a title attribute for tooltip
    const flexItems = container.querySelectorAll("[title]")
    const titles = Array.from(flexItems).map((el) => el.getAttribute("title"))
    expect(titles).toContain("Dashboard")
    expect(titles).toContain("The Lab")
  })
})
