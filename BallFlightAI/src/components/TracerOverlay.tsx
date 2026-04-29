import React from 'react';
import Svg, { Path } from 'react-native-svg';
import { TrackedPoint } from '@/types';
import { PremiumTheme } from '@/theme/premiumTheme';

type Props = {
  points: TrackedPoint[];
  color?: string;
  thickness?: number;
};

const toPath = (points: TrackedPoint[]) => {
  if (!points.length) {
    return '';
  }

  const [first, ...rest] = points;
  return `M ${first.x} ${first.y} ${rest.map((p) => `L ${p.x} ${p.y}`).join(' ')}`;
};

export function TracerOverlay({ points, color = PremiumTheme.colors.tracerGold, thickness = 4 }: Props) {
  if (!points.length) {
    return null;
  }

  return (
    <Svg style={{ position: 'absolute', inset: 0 }}>
      <Path
        d={toPath(points)}
        stroke={color}
        strokeWidth={thickness}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}
