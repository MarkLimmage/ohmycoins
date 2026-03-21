import { describe, expect, it, vi } from "vitest"
import { renderWithProviders } from "@/test-utils"

// Mock LabGrid to avoid deep dependency tree
vi.mock("./components/LabGrid", () => ({
  LabGrid: () => <div data-testid="lab-grid">LabGrid</div>,
}))

import { LabSessionView } from "./LabSessionView"

describe("LabSessionView", () => {
  it("renders LabGrid", () => {
    const { getByTestId } = renderWithProviders(<LabSessionView />)
    expect(getByTestId("lab-grid")).toBeInTheDocument()
  })

  it("does NOT render LabHeader (H4: removed)", () => {
    const { container } = renderWithProviders(<LabSessionView />)
    // LabHeader had a ReactFlow pipeline — verify no reactflow container
    expect(container.querySelector(".react-flow")).toBeNull()
    // Also verify no LabHeader text
    expect(container.textContent).not.toContain("Pipeline")
  })
})
