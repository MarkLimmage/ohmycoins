import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import { useLabWebSocket } from '../hooks/useLabWebSocket';

// Define the Cell structure for the Grid
export interface LabCell {
  id: string;
  type: 'code' | 'markdown' | 'plotly' | 'output' | 'error' | 'thought' | 'tool' | 'result' | 'blueprint' | 'metric';
  content: string; // text, code, or JSON string for plotly
  metadata?: any;
  status: 'queued' | 'running' | 'completed' | 'failed';
  timestamp?: string;
  executionTime?: number;
}

interface LabState {
  cells: LabCell[];
  sessionId: string | null;
  isConnected: boolean;
  isDone: boolean;
  sessionStatus: string | null;
  blueprint: any | null;
  metrics: any[];
  stages: Record<string, string>;
}

type Action =
  | { type: 'SET_SESSION'; payload: string | null }
  | { type: 'ADD_CELL'; payload: LabCell }
  | { type: 'UPDATE_CELL'; payload: { id: string; updates: Partial<LabCell> } }
  | { type: 'CLEAR_CELLS' }
  | { type: 'SET_CONNECTION_STATUS'; payload: { isConnected: boolean; isDone: boolean; sessionStatus: string | null } }
  | { type: 'SET_BLUEPRINT'; payload: any }
  | { type: 'ADD_METRIC'; payload: any }
  | { type: 'UPDATE_STAGE_STATUS'; payload: { stageId: string; status: string } };

const initialState: LabState = {
  cells: [],
  sessionId: null,
  isConnected: false,
  isDone: false,
  sessionStatus: null,
  blueprint: null,
  metrics: [],
  stages: {},
};

function labReducer(state: LabState, action: Action): LabState {
  switch (action.type) {
    case 'SET_SESSION':
      return { ...state, sessionId: action.payload, cells: [], blueprint: null, metrics: [], stages: {} };
    case 'ADD_CELL':
      // Deduplicate by ID
      if (state.cells.find(c => c.id === action.payload.id)) return state;
      return { ...state, cells: [...state.cells, action.payload] };
    case 'UPDATE_CELL':
      return {
        ...state,
        cells: state.cells.map((cell) =>
          cell.id === action.payload.id ? { ...cell, ...action.payload.updates } : cell
        ),
      };
    case 'CLEAR_CELLS':
      return { ...state, cells: [], blueprint: null, metrics: [], stages: {} };
    case 'SET_CONNECTION_STATUS':
      return { ...state, ...action.payload };
    case 'SET_BLUEPRINT':
      return { ...state, blueprint: action.payload };
    case 'ADD_METRIC':
         // Deduplicate by name if metric has name
         // payload is expected to have 'name' property as per previous implementation
         const newMetric = action.payload;
         const otherMetrics = state.metrics.filter(m => m.name !== newMetric.name);
         return { ...state, metrics: [...otherMetrics, newMetric] };
    case 'UPDATE_STAGE_STATUS':
         return { ...state, stages: { ...state.stages, [action.payload.stageId]: action.payload.status } };
    default:
      return state;
  }
}

const LabContext = createContext<{
  state: LabState;
  dispatch: React.Dispatch<Action>;
} | undefined>(undefined);

export function LabProvider({ children, sessionId }: { children: ReactNode; sessionId: string | null }) {
  const [state, dispatch] = useReducer(labReducer, initialState);
  
  // Use the existing hook to get messages
  const { messages, isConnected, isDone, sessionStatus } = useLabWebSocket({
    sessionId,
    enabled: !!sessionId
  });

  useEffect(() => {
    dispatch({ type: 'SET_SESSION', payload: sessionId });
  }, [sessionId]);

  useEffect(() => {
    dispatch({ type: 'SET_CONNECTION_STATUS', payload: { isConnected, isDone, sessionStatus } });
  }, [isConnected, isDone, sessionStatus]);

  // Process messages into cells
  useEffect(() => {
    messages.forEach(msg => {
       // Support both AgentMessage (legacy) and API Contract (event_type)
       const rawMsg = msg as any;
       const eventType = rawMsg.event_type || msg.type;
       
       // API Contract: status_update
       if (eventType === 'status_update' && rawMsg.stage) {
            // Assume payload has status, or use event itself as trigger
            // Payload might look like { status: "ACTIVE" } or just be the event
            const status = rawMsg.payload?.status || rawMsg.payload || 'ACTIVE';
            dispatch({ 
                type: 'UPDATE_STAGE_STATUS', 
                payload: { stageId: rawMsg.stage, status: typeof status === 'string' ? status : 'ACTIVE' } 
            });
            // Don't create a cell for status updates unless we want to log them
            return;
       }

       let cellType: LabCell['type'] = 'output';
       
       // Map defines to LabCell types
       if (eventType === 'thought') cellType = 'markdown'; 
       else if (eventType === 'tool') cellType = 'code';
       else if (eventType === 'result') cellType = 'output';
       else if (eventType === 'output') cellType = 'output';
       else if (eventType === 'blueprint') cellType = 'blueprint';
       else if (eventType === 'metric') cellType = 'metric';
       else if (eventType === 'render_output') cellType = 'output'; // API Contract
       else if (eventType === 'stream_chat') cellType = 'markdown'; // API Contract
       
       // Priority to metadata format overrides
       if (msg.metadata?.format === 'plotly') cellType = 'plotly';
       else if (msg.metadata?.format === 'markdown') cellType = 'markdown';
       
       // Content extraction
       let content = msg.content;
       if (eventType === 'stream_chat') {
           content = rawMsg.payload?.text_delta || "";
           // TODO: Handle streaming append if needed. For now assume full message or separate chunks.
       }
       
       const cell: LabCell = {
           id: msg.id || `${Date.now()}-${Math.random()}`,
           type: cellType,
           content: content || JSON.stringify(rawMsg.payload) || "",
           metadata: msg.metadata || rawMsg.payload,
           status: msg.metadata?.error ? 'failed' : 'completed',
           timestamp: msg.timestamp
       };
       
       dispatch({ type: 'ADD_CELL', payload: cell });

       if ((eventType === 'blueprint' || eventType === 'render_output') && (msg.metadata || rawMsg.payload)) {
            // Check if payload is blueprint
            const potentialBlueprint = msg.metadata || rawMsg.payload;
            // Very naive check
            if (potentialBlueprint && potentialBlueprint.target && potentialBlueprint.spec) {
                 dispatch({ type: 'SET_BLUEPRINT', payload: potentialBlueprint });
            }
            // Or if content is JSON blueprint
            try {
                if (content && content.startsWith('{')) {
                    const bp = JSON.parse(content);
                    if (bp.target) dispatch({ type: 'SET_BLUEPRINT', payload: bp });
                }
            } catch (e) {}
       }

       if (eventType === 'metric' && (msg.metadata || rawMsg.payload)) {
            try {
                const metric = typeof content === 'string' ? JSON.parse(content) : (msg.metadata || rawMsg.payload);
                dispatch({ type: 'ADD_METRIC', payload: metric });
            } catch (err) {
                 console.error("Failed to parse metric:", err);
            }
       }
    });
  }, [messages]);


  return (
    <LabContext.Provider value={{ state, dispatch }}>
      {children}
    </LabContext.Provider>
  );
}

export const useLabContext = () => {
  const context = useContext(LabContext);
  if (!context) {
    throw new Error('useLabContext must be used within a LabProvider');
  }
  return context;
};
