import { screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import type { AgentSessionPublic } from "@/client"
import { renderWithProviders } from "@/test-utils"
import { SessionDrawer } from "./SessionDrawer"

// Mock child components to isolate drawer tests
vi.mock("./SessionList", () => ({
  SessionList: ({
    sessions,
    onSelect,
  }: {
    sessions: unknown[]
    onSelect: (id: string) => void
  }) => (
    <div data-testid="session-list">
      {(sessions as { id: string }[]).map((s) => (
        <button type="button" key={s.id} onClick={() => onSelect(s.id)}>
          {s.id}
        </button>
      ))}
    </div>
  ),
}))

vi.mock("./SessionCreateForm", () => ({
  SessionCreateForm: ({ isOpen }: { isOpen: boolean }) =>
    isOpen ? <div data-testid="create-form">Create Form</div> : null,
}))

function makeSessions(
  overrides: Partial<AgentSessionPublic>[] = [],
): AgentSessionPublic[] {
  return overrides.map((o, i) => ({
    id: `session-${i}`,
    user_goal: `Goal ${i}`,
    status: "completed",
    user_id: "user-1",
    created_at: "2026-03-22T00:00:00Z",
    updated_at: "2026-03-22T00:00:00Z",
    ...o,
  }))
}

describe("SessionDrawer", () => {
  it("renders the trigger button with Open sessions label", () => {
    renderWithProviders(
      <SessionDrawer
        sessions={[]}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        open={false}
        onOpenChange={vi.fn()}
      />,
    )
    expect(
      screen.getByRole("button", { name: "Open sessions" }),
    ).toBeInTheDocument()
  })

  it("shows active session count badge when sessions are running", () => {
    const sessions = makeSessions([
      { status: "running" },
      { status: "completed" },
      { status: "pending" },
    ])

    renderWithProviders(
      <SessionDrawer
        sessions={sessions}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        open={false}
        onOpenChange={vi.fn()}
      />,
    )
    // Badge should show 2 (running + pending)
    expect(screen.getByText("2")).toBeInTheDocument()
  })

  it("does not show badge when no active sessions", () => {
    const sessions = makeSessions([
      { status: "completed" },
      { status: "completed" },
    ])

    renderWithProviders(
      <SessionDrawer
        sessions={sessions}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        open={false}
        onOpenChange={vi.fn()}
      />,
    )
    // Badge text would contain a number; no running/pending sessions → no badge
    expect(screen.queryByText("1")).not.toBeInTheDocument()
    expect(screen.queryByText("2")).not.toBeInTheDocument()
  })

  it("renders drawer content with Sessions title and New Session button when open", () => {
    renderWithProviders(
      <SessionDrawer
        sessions={makeSessions([{ status: "completed" }])}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        open={true}
        onOpenChange={vi.fn()}
      />,
    )
    expect(screen.getByText("Sessions")).toBeInTheDocument()
    expect(screen.getByText("New Session")).toBeInTheDocument()
  })

  it("renders SessionList inside the drawer when open", () => {
    renderWithProviders(
      <SessionDrawer
        sessions={makeSessions([{ status: "running" }])}
        selectedId={null}
        onSelect={vi.fn()}
        onDelete={vi.fn()}
        open={true}
        onOpenChange={vi.fn()}
      />,
    )
    // Chakra portals may duplicate content; at least one session-list should exist
    expect(screen.getAllByTestId("session-list").length).toBeGreaterThanOrEqual(
      1,
    )
  })

  it("calls onSelect and closes drawer when a session is selected", async () => {
    const onSelect = vi.fn()
    const onOpenChange = vi.fn()

    renderWithProviders(
      <SessionDrawer
        sessions={makeSessions([{ id: "abc-123", status: "completed" }])}
        selectedId={null}
        onSelect={onSelect}
        onDelete={vi.fn()}
        open={true}
        onOpenChange={onOpenChange}
      />,
    )

    const sessionBtn = screen.getByText("abc-123")
    sessionBtn.click()

    expect(onSelect).toHaveBeenCalledWith("abc-123")
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })
})
