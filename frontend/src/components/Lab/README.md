# Lab Components

This directory contains components for the experimental Lab feature of Oh My Coins, including real-time agent execution monitoring.

## Components

### AgentTerminal

A streaming console component for displaying real-time agent logs with full accessibility support.

#### Features

- **WebSocket Streaming**: Real-time message streaming from agent sessions
- **Virtual Scrolling**: Performance-optimized message display (uses CSS overflow for MVP)
- **Auto-scroll**: Automatically scrolls to latest messages with manual override
- **Search**: Full-text search across all messages (Ctrl/Cmd+F)
- **Export**: Download transcript as text file or copy to clipboard
- **Accessibility**: WCAG 2.1 AA compliant with ARIA live regions and keyboard navigation

#### Usage

```tsx
import { AgentTerminal } from "@/components/Lab"

function LabPage() {
  return (
    <AgentTerminal
      sessionId="abc123"
      streamUrl="wss://api.example.com/agent/stream"
      allowInteraction={true}
      onExport={() => console.log("Export clicked")}
      onCancel={() => console.log("Cancel clicked")}
    />
  )
}
```

#### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `sessionId` | `string` | Yes | Unique identifier for the agent session |
| `streamUrl` | `string` | Yes | WebSocket URL for message streaming |
| `allowInteraction` | `boolean` | Yes | Enable/disable interactive controls |
| `onExport` | `() => void` | No | Custom export handler (default: download as file) |
| `onCancel` | `() => void` | No | Handler for canceling the session |

#### Keyboard Shortcuts

- **Ctrl/Cmd+F**: Open search
- **Ctrl/Cmd+C**: Copy transcript to clipboard (when search is closed)
- **Esc**: Close search
- **Tab**: Navigate between controls
- **Enter/Space**: Activate buttons

### AgentMessage

Individual message component with type-specific styling and metadata display.

#### Message Types

1. **thought**: Agent reasoning (gray, italic)
2. **tool**: Tool execution (blue, with tool icon)
3. **result**: Tool result (green for success, red for error)
4. **input_request**: Requesting user input (amber)
5. **output**: Final output (bold, highlighted background)

#### Features

- Timestamp display (HH:mm:ss.SSS)
- Type-specific icons and colors
- Syntax highlighting for code blocks
- Metadata display (tool name, execution time, errors)
- ANSI color mapping (simplified)

#### Message Format

```typescript
{
  id: "msg-123",
  type: "tool",
  content: "Executing search query...",
  timestamp: "2024-01-24T10:30:45.123Z",
  metadata: {
    tool_name: "search_files",
    execution_time: 245,
    error?: "Optional error message"
  }
}
```

## Accessibility Features

### ARIA Support

- **Live regions**: Messages container has `aria-live="polite"` for screen reader announcements
- **Role attributes**: Proper semantic roles (`log`, `region`, etc.)
- **Labels**: All interactive elements have `aria-label` attributes
- **Focus management**: 2px outline on focused elements

### Keyboard Navigation

All functionality is accessible via keyboard:
- Tab navigation between all controls
- Enter/Space to activate buttons
- Arrow keys for scrolling (native behavior)
- Keyboard shortcuts for common actions

### Visual Indicators

- Connection status indicator (green/red dot)
- Clear focus indicators on all interactive elements
- High contrast colors for message types
- Readable monospace font for content

## Performance Considerations

### Current Implementation (MVP)

- Uses CSS `overflow-y: auto` for scrolling
- Handles up to ~1000 messages efficiently
- Auto-scroll optimization to prevent unnecessary renders
- Debounced scroll event handling

### Future Enhancements

For handling 10,000+ messages:
- Integrate `react-window` or `react-virtuoso` for virtual scrolling
- Implement message pagination
- Add message filtering/grouping
- Optimize WebSocket message batching

## WebSocket Protocol

### Connection

```typescript
const ws = new WebSocket(streamUrl)
ws.send(JSON.stringify({ 
  action: "subscribe", 
  sessionId: "abc123" 
}))
```

### Message Format

```json
{
  "id": "msg-123",
  "type": "tool",
  "content": "Message content",
  "timestamp": "2024-01-24T10:30:45.123Z",
  "metadata": {
    "tool_name": "search_files",
    "execution_time": 245
  }
}
```

### Error Handling

- Connection errors: Display error toast
- Parse errors: Log to console, skip message
- Disconnection: Update UI status indicator

## Styling

### Theme Integration

Uses Chakra UI tokens and semantic colors:
- Background: `gray.900` (terminal dark)
- Borders: `whiteAlpha.300`
- Text: `gray.200` for primary, `gray.400` for secondary
- Scrollbar: Custom webkit styling for dark theme

### Responsive Design

- Container adapts to parent dimensions
- Minimum recommended height: 400px
- Minimum recommended width: 600px
- Mobile-friendly button sizes and touch targets

## Testing

### Manual Testing Checklist

- [ ] WebSocket connection and disconnection
- [ ] Message rendering for all types
- [ ] Search functionality
- [ ] Copy to clipboard
- [ ] Export to file
- [ ] Auto-scroll behavior
- [ ] Jump to latest button
- [ ] Keyboard shortcuts (Ctrl+F, Ctrl+C, Esc)
- [ ] Tab navigation through all controls
- [ ] Screen reader announcements (use NVDA/JAWS)
- [ ] Focus indicators visible
- [ ] Cancel button (if provided)

### Mock Data for Testing

```typescript
const mockMessages: AgentMessage[] = [
  {
    id: "1",
    type: "thought",
    content: "Analyzing the request...",
    timestamp: new Date().toISOString(),
  },
  {
    id: "2",
    type: "tool",
    content: "Searching codebase for 'AgentTerminal'",
    timestamp: new Date().toISOString(),
    metadata: { tool_name: "search_files", execution_time: 123 },
  },
  {
    id: "3",
    type: "result",
    content: "Found 3 files matching the query",
    timestamp: new Date().toISOString(),
  },
]
```

## Known Limitations

1. **Virtual Scrolling**: Not implemented in MVP, may have performance issues with 10,000+ messages
2. **ANSI Colors**: Simplified color mapping, doesn't support full ANSI escape sequences
3. **WebSocket Reconnection**: No automatic reconnection on disconnect
4. **Message Persistence**: Messages lost on component unmount
5. **Input Interaction**: `input_request` type displays but doesn't handle user input yet

## Future Enhancements

- [ ] Virtual scrolling with react-window
- [ ] Message filtering by type
- [ ] Message grouping/collapsing
- [ ] Full ANSI color support with library
- [ ] WebSocket auto-reconnection
- [ ] Message persistence (IndexedDB)
- [ ] Interactive input handling
- [ ] Dark/light theme toggle
- [ ] Customizable color schemes
- [ ] Message bookmarking
- [ ] Regex search support
- [ ] Export to multiple formats (JSON, Markdown)

## Dependencies

- `@chakra-ui/react`: UI components
- `react-icons`: Icon library
- `date-fns`: Timestamp formatting
- Native WebSocket API: Real-time streaming

## Related Components

- **Agent**: LLM credential management
- **Floor**: Trading floor components
- **Ledgers**: Transaction tracking

## Support

For issues or questions about these components, please refer to:
- Main README: `/frontend/README.md`
- Architecture docs: `/docs/architecture/`
- Accessibility requirements: See REQ-UX-004, REQ-UX-005, REQ-UX-008
