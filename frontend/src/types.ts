export interface EnvironmentalProfile {
  soil?: { ph?: number; organic_carbon?: number; moisture?: string };
  climate?: { temperature?: number; rainfall?: string };
  land?: { land_use?: string; crop?: string; cropping_pattern?: string };
  biodiversity?: { species_richness?: string; habitat_diversity?: string };
  human_impact?: { pollution?: string; deforestation?: string };
}

export interface Recommendation {
  recommendation: string;
  why: string;
  affected_metrics: string[];
  time_horizon: string;
  confidence: string;
}

export interface Evidence {
  id: string;
  document_id: string;
  text: string;
  similarity: number;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  needs_clarification: boolean;
  can_reason: boolean;
  missing_fields: string[];
  profile: EnvironmentalProfile;
  recommendation: Recommendation | null;
  retrieved_evidence: Evidence[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}