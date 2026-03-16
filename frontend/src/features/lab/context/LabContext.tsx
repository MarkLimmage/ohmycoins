// Workstream E: Lab Context Refactor (Scientific Grid)
import React, { createContext, useContext, useReducer, ReactNode, useEffect, useCallback } from 'react';
import { useLabWebSocket } from '../hooks/useLabWebSocket';
import { useRehydration } from '../hooks/useRehydration';
import { LabState, LabEvent, LabCell, LabStage, ActionRequest } from '../types';

type Action =
  | { type: 'SET_SESSION'; payload: string | null }
  | { type: 'REHYDRATE'; payload: { ledger: LabEvent[]; lastSequenceId: number } }
  | { type: 'PROCESS_EVENT'; payload: LabEvent }
  | { type: 'SET_CONNECTION_STATUS'; payload: { isConnected: boolean } }
  | { type: 'SET_DONE'; payload: boolean }
  | { type: 'CLEAR_ACTION' };

const initialState: LabState = {
  sessionId: null,
  stages: {
    'BUSINESS_UNDERSTANDING': [],
    'DATA_ACQUISITION': [],
    'PREPARATION': [],
    'EXPLORATION': [],
    'MODELING': [],
    'EVALUATION': [],
    'DEPLOYMENT': [],
  },
  activeStages: new Set(),
  lastSequenceId: 0,
  isConnected: false,
  isDone: false,
  pendingAction: null,
  metrics: [],
  blueprint: null,
};

function labReducer(state: LabState, action: Action): LabState {
  switch (action.type) {
    case 'SET_SESSION':
      return { 
        ...initialState, 
        sessionId: action.payload 
      };

    case 'SET_CONNECTION_STATUS':
      return { ...state, isConnected: action.payload.isConnected };

    case 'SET_DONE':
      return { ...state, isDone: action.payload };

    case 'CLEAR_ACTION':
        return { ...state, pendingAction: null };

    case 'REHYDRATE': {
      // E4: Rehydration logic
      // Sort ledger by sequence_id
      const sortedLedger = [...action.payload.ledger].sort((a, b) => a.sequence_id - b.sequence_id);
      
      // Replay events to build state
      let newState = { ...state, lastSequenceId: action.payload.lastSequenceId };
      
      for (const event of sortedLedger) {
        newState = processEvent(newState, event);
      }
      return newState;
    }

    case 'PROCESS_EVENT': {
      const event = action.payload;

      // E2: Sequence-ID Ordering - Discard out-of-order events
      if (event.sequence_id <= state.lastSequenceId) {
        console.warn(`Discarding out-of-order event ${event.sequence_id} (current: ${state.lastSequenceId})`);
        return state;
      }

      return processEvent(state, event);
    }

    default:
      return state;
  }
}

function processEvent(state: LabState, event: LabEvent): LabState {
  const { event_type, stage, payload, sequence_id, timestamp } = event;
  
  const newState = { 
      ...state, 
      lastSequenceId: Math.max(state.lastSequenceId, sequence_id) 
  };

  // Update active stages
  if (stage && !newState.activeStages.has(stage)) {
       const newActive = new Set(newState.activeStages);
       newActive.add(stage);
       newState.activeStages = newActive;
  }

  // Handle Action Requests
   if (event_type === 'action_request') {
      return {
        ...newState,
        pendingAction: {
          action_id: payload.action_id,
          description: payload.description,
          options: payload.options
        }
      };
   }

   // Handle Status Updates 
   if (event_type === 'status_update') {
      if (payload.status === 'COMPLETE' || payload.status === 'completed') {
          // If needed, mark stage complete
      }
      return newState;
   }

   // For render_output and fallback for others: Map to Cells
  const targetStage = stage || 'BUSINESS_UNDERSTANDING';
  const currentStageCells = newState.stages[targetStage] || [];
  
  // Check duplicate by sequence_id
  if (currentStageCells.some(c => c.id === String(sequence_id))) {
      return newState;
  }

  const newCell: LabCell = {
    id: String(sequence_id),
    stage: targetStage,
    type: payload.mime_type || 'text/markdown',
    content: payload.content || '',
    timestamp,
    metadata: payload.metadata
  };

  // Side-effect: Populate legacy state for dependent components
  if (newCell.type === 'application/json+blueprint') {
      try {
        newState.blueprint = newCell.content; 
      } catch (e) {
          console.error("Failed to parse blueprint content:", e);
      }
  }

  return {
    ...newState,
    stages: {
      ...newState.stages,
      [targetStage]: [...currentStageCells, newCell]
    }
  };
}

const LabContext = createContext<{
  state: LabState;
  dispatch: React.Dispatch<Action>;
  sendMessage: (message: any) => void;
  isLoading: boolean;
} | undefined>(undefined);

export function LabProvider({ children, sessionId }: { children: ReactNode; sessionId: string | null }) {
  const [state, dispatch] = useReducer(labReducer, initialState);
  const { rehydrate, isRehydrating } = useRehydration();

  // Handle WebSocket events
  const onEvent = useCallback((event: LabEvent) => {
    dispatch({ type: 'PROCESS_EVENT', payload: event });
  }, []);

  const { isConnected, sendMessage } = useLabWebSocket({
    sessionId,
    enabled: !!sessionId,
    onEvent
  });

  // Sync connection status
  useEffect(() => {
    dispatch({ type: 'SET_CONNECTION_STATUS', payload: { isConnected } });
  }, [isConnected]);

  // Handle Session Change
  useEffect(() => {
    dispatch({ type: 'SET_SESSION', payload: sessionId });
    if (sessionId) {
      // E4: Rehydration on mount
      rehydrate(sessionId).then(data => {
        if (data) {
          dispatch({ 
            type: 'REHYDRATE', 
            payload: { 
              ledger: data.event_ledger, 
              lastSequenceId: data.last_sequence_id 
            } 
          });
        }
      });
    }
  }, [sessionId, rehydrate]);

  return (
    <LabContext.Provider value={{ state, dispatch, sendMessage, isLoading: isRehydrating }}>
      {children}
    </LabContext.Provider>
  );
}

export const useLabContext = () => {
    const context = useContext(LabContext);
    if (context === undefined) {
      throw new Error('useLabContext must be used within a LabProvider');
    }
    return context;
};
