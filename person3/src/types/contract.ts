export interface RiskScores {
  acute_distress: number;
  depression: number;
  self_harm_risk: number;
  fear_of_retaliation: number;
  intimidation: number;
  dissociation: number;
  social_isolation: number;
  chronic_trauma_indicators: number;
}

export interface RiskConfidence {
  acute_distress?: number;
  depression?: number;
  self_harm_risk?: number;
  fear_of_retaliation?: number;
  intimidation?: number;
  dissociation?: number;
  social_isolation?: number;
  chronic_trauma_indicators?: number;
  [key: string]: number | undefined;
}

export interface MatchedEvidence {
  acute_distress?: string[];
  depression?: string[];
  self_harm_risk?: string[];
  fear_of_retaliation?: string[];
  intimidation?: string[];
  dissociation?: string[];
  social_isolation?: string[];
  chronic_trauma_indicators?: string[];
  [key: string]: string[] | undefined;
}

export interface RiskVector {
  scores: RiskScores;
  confidence: RiskConfidence;
  matched_evidence: MatchedEvidence;
}

export interface SVI {
  value: number;
  bucket: 'low' | 'moderate' | 'high' | 'critical';
}

export interface SilenceEvent {
  start_sec: number;
  duration_sec: number;
  placement: 'mid_sentence' | 'pause' | 'end_sentence';
}

export interface TranscriptUpdateEvent {
  type: 'transcript_update';
  text: string;
  timestamp?: string;
  risk_vector: RiskVector;
  svi: SVI;
  silence_events: SilenceEvent[];
  overall_confidence?: number;
}

export interface ActionState {
  action: 'counseling' | 'legal_aid' | 'police_intervention' | 'witness_protection' | 'emergency_escalation';
  state: 'not_requested' | 'awaiting_senior' | 'approved' | 'rejected' | 'in_progress';
  requires_senior: boolean;
}

export interface ActionUpdateEvent {
  type: 'action_update';
  action: ActionState;
}

export interface HandoffReceivedEvent {
  type: 'handoff_received';
  call_id: string;
  from_agent: string;
  reason: string;
  risk_vector: RiskVector;
  svi: SVI;
  evidence: MatchedEvidence;
  timeline: { time: string; text: string }[] | string[];
  consent_summary: Record<string, boolean>;
  silence_events: SilenceEvent[];
  action_history: { action_type: string; state: string }[];
}

export type SharedContractMessage = TranscriptUpdateEvent | ActionUpdateEvent | HandoffReceivedEvent;
