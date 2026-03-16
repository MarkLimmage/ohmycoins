// Workstream E: Lab Types
// Spec: WORKER_MISSION.md v1.2

export type LabStage = 
  | 'BUSINESS_UNDERSTANDING'
  | 'DATA_ACQUISITION'
  | 'PREPARATION'
  | 'EXPLORATION'
  | 'MODELING'
  | 'EVALUATION'
  | 'DEPLOYMENT';

export type LabMimeType =
  | 'text/markdown'
  | 'application/vnd.plotly.v1+json'
  | 'application/json+blueprint'
  | 'application/json+tearsheet'
  | 'image/png';

export interface LabEventPayload {
  [key: string]: any;
}

export interface LabEvent {
  event_type: 'stream_chat' | 'status_update' | 'render_output' | 'error' | 'action_request';
  stage: LabStage;
  sequence_id: number;
  timestamp: string; // ISO-8601
  payload: LabEventPayload;
}

export interface LabCell {
  id: string; // sequence_id as string
  stage: LabStage;
  type: LabMimeType;
  content: any;
  timestamp: string;
  metadata?: any;
}

export interface ActionRequest {
  action_id: string;
  description: string;
  options: string[];
}

export interface LabState {
  sessionId: string | null;
  // E1: Stage-Isolated Grid - Map<StageID, LabCell[]>
  stages: Record<LabStage, LabCell[]>; 
  activeStages: Set<LabStage>;
  lastSequenceId: number;
  isConnected: boolean;
  isDone: boolean;
  pendingAction: ActionRequest | null;
  metrics: any[];
  blueprint: any | null;
}
