// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { CollectorCard } from '../CollectorCard'
import { CollectorInstance } from '../types'
import { ChakraProvider, defaultSystem } from '@chakra-ui/react'

const renderWithChakra = (ui: React.ReactElement) => {
  return render(
    <ChakraProvider value={defaultSystem}>
      {ui}
    </ChakraProvider>
  )
}

// Mock Recharts to avoid responsive container issues in tests
vi.mock('recharts', () => {
  const OriginalModule = vi.importActual('recharts');
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: any }) => <div data-testid="responsive-container">{children}</div>,
    LineChart: ({ children }: { children: any }) => <div data-testid="line-chart">{children}</div>,
    Line: () => <div data-testid="line" />,
  };
});

// Mock hooks
const mockUseCollectorStats = vi.fn()
vi.mock('../hooks', () => ({
  useCollectorStats: (id: string) => mockUseCollectorStats(id)
}))

const mockInstance: CollectorInstance = {
  id: '1',
  name: 'Test Collector',
  plugin_id: 'test-plugin',
  status: 'running',
  config: {},
  last_run: '2024-01-01T12:00:00Z',
  next_run: null,
  is_active: true,
  error_count: 0,
  success_count: 10
}

describe('CollectorCard', () => {
  const mockOnEdit = vi.fn()
  const mockOnToggle = vi.fn()
  const mockOnDelete = vi.fn()

  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseCollectorStats.mockReturnValue({
      data: [
        { timestamp: '2024-01-01T10:00:00Z', count: 10 },
        { timestamp: '2024-01-01T11:00:00Z', count: 20 },
        { timestamp: '2024-01-01T12:00:00Z', count: 30 }
      ]
    })
  })

  // Basic rendering test
  it('renders collector name and plugin', () => {
    renderWithChakra(
        <CollectorCard 
          instance={mockInstance} 
          pluginName="Test Plugin"
          onEdit={mockOnEdit}
          onToggle={mockOnToggle}
          onDelete={mockOnDelete}
        />
    )
    
    expect(screen.getByText('Test Collector')).toBeInTheDocument()
    expect(screen.getByText('Test Plugin')).toBeInTheDocument()
    expect(screen.getByText('running')).toBeInTheDocument()
  })

  // Visualization test (Sparkline)
  it('renders the sparkline visualization', () => {
    renderWithChakra(
        <CollectorCard 
          instance={mockInstance} 
          pluginName="Test Plugin"
          onEdit={mockOnEdit}
          onToggle={mockOnToggle}
          onDelete={mockOnDelete}
        />
    )
    
    // Check if Recharts components are present (mocked)
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
  })

  // Interaction tests
  it('calls onEdit when edit button is clicked', () => {
    renderWithChakra(
        <CollectorCard 
          instance={mockInstance} 
          pluginName="Test Plugin"
          onEdit={mockOnEdit}
          onToggle={mockOnToggle}
          onDelete={mockOnDelete}
        />
    )
    
    const editButton = screen.getByLabelText('Edit')
    fireEvent.click(editButton)
    expect(mockOnEdit).toHaveBeenCalled()
  })

  it('calls onToggle when pause/resume button is clicked', () => {
    renderWithChakra(
        <CollectorCard 
          instance={mockInstance} 
          pluginName="Test Plugin"
          onEdit={mockOnEdit}
          onToggle={mockOnToggle}
          onDelete={mockOnDelete}
        />
    )
    
    const toggleButton = screen.getByLabelText('Pause') // Since is_active=true
    fireEvent.click(toggleButton)
    expect(mockOnToggle).toHaveBeenCalled()
  })

    it('calls onDelete when delete button is clicked', () => {
    renderWithChakra(
        <CollectorCard 
          instance={mockInstance} 
          pluginName="Test Plugin"
          onEdit={mockOnEdit}
          onToggle={mockOnToggle}
          onDelete={mockOnDelete}
        />
    )
    
    const deleteButton = screen.getByLabelText('Delete')
    fireEvent.click(deleteButton)
    expect(mockOnDelete).toHaveBeenCalled()
  })
})
