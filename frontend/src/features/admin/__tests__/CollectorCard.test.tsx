// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest"
import { ChakraProvider, defaultSystem } from "@chakra-ui/react"
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { CollectorCard } from "../CollectorCard"
import type { CollectorCardData } from "../types"

const renderWithChakra = (ui: React.ReactElement) => {
  return render(<ChakraProvider value={defaultSystem}>{ui}</ChakraProvider>)
}

// Mock Recharts to avoid responsive container issues in tests
vi.mock("recharts", () => {
  const OriginalModule = vi.importActual("recharts")
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: any }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
    LineChart: ({ children }: { children: any }) => (
      <div data-testid="line-chart">{children}</div>
    ),
    Line: () => <div data-testid="line" />,
  }
})

// Mock hooks
const mockUseCollectorStats = vi.fn()
vi.mock("../hooks", () => ({
  useCollectorStats: (id: string) => mockUseCollectorStats(id),
}))

const mockCard: CollectorCardData = {
  plugin_id: "test-plugin",
  plugin_name: "Test Plugin",
  plugin_description: "Test plugin description",
  plugin_schema: {},
  instance_id: "1",
  instance_name: "Test Collector",
  status: "success",
  config: {},
  schedule_cron: "*/15 * * * *",
  last_run: "2024-01-01T12:00:00Z",
  is_active: true,
  success_rate: 95.5,
  total_records: 150,
  avg_duration: 1.5,
  total_runs: 20,
}

describe("CollectorCard", () => {
  const mockOnEdit = vi.fn()
  const mockOnToggle = vi.fn()
  const mockOnRun = vi.fn()

  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseCollectorStats.mockReturnValue({
      data: [
        { timestamp: "2024-01-01T10:00:00Z", count: 10 },
        { timestamp: "2024-01-01T11:00:00Z", count: 20 },
        { timestamp: "2024-01-01T12:00:00Z", count: 30 },
      ],
    })
  })

  // Basic rendering test
  it("renders collector name and plugin", () => {
    renderWithChakra(
      <CollectorCard
        card={mockCard}
        onEdit={mockOnEdit}
        onToggle={mockOnToggle}
        onRun={mockOnRun}
      />,
    )

    expect(screen.getByText("Test Plugin")).toBeInTheDocument()
    expect(screen.getByText("*/15 * * * *")).toBeInTheDocument()
  })

  // Visualization test (Sparkline)
  it("renders the sparkline visualization", () => {
    renderWithChakra(
      <CollectorCard
        card={mockCard}
        onEdit={mockOnEdit}
        onToggle={mockOnToggle}
        onRun={mockOnRun}
      />,
    )

    // Check if Recharts components are present (mocked)
    expect(screen.getByTestId("responsive-container")).toBeInTheDocument()
    expect(screen.getByTestId("line-chart")).toBeInTheDocument()
  })

  // Interaction tests
  it("calls onEdit when edit button is clicked", () => {
    renderWithChakra(
      <CollectorCard
        card={mockCard}
        onEdit={mockOnEdit}
        onToggle={mockOnToggle}
        onRun={mockOnRun}
      />,
    )

    const editButton = screen.getByLabelText("Edit")
    fireEvent.click(editButton)
    expect(mockOnEdit).toHaveBeenCalled()
  })

  it("calls onToggle when switch is clicked", () => {
    renderWithChakra(
      <CollectorCard
        card={mockCard}
        onEdit={mockOnEdit}
        onToggle={mockOnToggle}
        onRun={mockOnRun}
      />,
    )

    const switchControl = screen.getByRole("checkbox")
    fireEvent.click(switchControl)
    expect(mockOnToggle).toHaveBeenCalled()
  })

  it("calls onRun when run button is clicked", () => {
    renderWithChakra(
      <CollectorCard
        card={mockCard}
        onEdit={mockOnEdit}
        onToggle={mockOnToggle}
        onRun={mockOnRun}
      />,
    )

    const runButton = screen.getByLabelText("Run Manual Trigger")
    fireEvent.click(runButton)
    expect(mockOnRun).toHaveBeenCalled()
  })
})
