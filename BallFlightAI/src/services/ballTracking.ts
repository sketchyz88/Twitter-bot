import { TraceResult } from '@/types';

/**
 * Placeholder inference pipeline.
 * Replace with native OpenCV + model inference bridge for production.
 */
export async function runBallTracking(videoUri: string): Promise<TraceResult> {
  console.log('Running tracking for', videoUri);

  return {
    points: [
      { x: 180, y: 540, frame: 0 },
      { x: 220, y: 480, frame: 4 },
      { x: 280, y: 420, frame: 8 },
      { x: 360, y: 370, frame: 12 },
      { x: 440, y: 340, frame: 16 },
    ],
    shotShape: 'draw',
    apexHeightMeters: 29.2,
    estimatedCarryYards: 261,
    launchDirectionDegrees: 2.3,
  };
}
