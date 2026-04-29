export type ShotShape = 'draw' | 'fade' | 'slice' | 'hook' | 'straight';

export type TrackedPoint = {
  x: number;
  y: number;
  frame: number;
};

export type TraceResult = {
  points: TrackedPoint[];
  shotShape: ShotShape;
  apexHeightMeters: number;
  estimatedCarryYards: number;
  launchDirectionDegrees: number;
};

export type SwingClip = {
  id: string;
  createdAt: string;
  club: string;
  sourceUri: string;
  tracedUri?: string;
  favorite: boolean;
  traceResult?: TraceResult;
};
