import { describe, expect, it, vi } from "vitest"
import { renderWithProviders } from "@/test-utils"

// Mock StageRowList to avoid deep dependency tree
vi.mock("./components/StageRowList", () => ({
  StageRowList: () => <div data-testid="stage-row-list">StageRowList</div>,
}))

import { LabSessionView } from "./LabSessionView"

describe("LabSessionView", () => {
  it("renders StageRowList", () => {
    const { getByTestId } = renderWithProviders(<LabSessionView />)
    expect(getByTestId("stage-row-list")).toBeInTheDocument()
  })

  it("does NOT render LabHeader (H4: removed)", () => {
    const { container } = renderWithProviders(<LabSessionView />)
    // LabHeader had a ReactFlow pipeline — verify no reactflow container
    expect(container.querySelector(".react-flow")).toBeNull()
    // Also verify no LabHeader text
    expect(container.textContent).not.toContain("Pipeline")
  })
})
