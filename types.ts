
export enum FloodSeverity {
  LOW = 'Low',
  MEDIUM = 'Medium',
  HIGH = 'High',
  CRITICAL = 'Critical'
}

export interface RegionData {
  id: string;
  name: string;
  submergedArea: number; // in hectares
  rainfall: number; // in mm
  avgDepth: number; // in meters
  severity: FloodSeverity;
  affectedPopulation: number;
  estimatedLoss: number; // in billion VND
}

export interface WeatherDay {
  date: string;
  rainfall: number;
  temperature: number;
}

export interface AIAnalysisResult {
  summary: string;
  riskAssessment: string;
  recommendations: string[];
  confidenceScore: number;
  estimatedTotalLoss: number;
}
