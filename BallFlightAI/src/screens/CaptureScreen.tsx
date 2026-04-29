import React, { useState } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { runBallTracking } from '@/services/ballTracking';
import { TraceResult } from '@/types';
import { TracerOverlay } from '@/components/TracerOverlay';
import { PremiumTheme } from '@/theme/premiumTheme';

export function CaptureScreen() {
  const [trace, setTrace] = useState<TraceResult | null>(null);

  const onMockTrack = async () => {
    const result = await runBallTracking('mock://swing.mov');
    setTrace(result);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>BallFlight AI</Text>
      <Text style={styles.subtitle}>Elite golf shot tracer for creators.</Text>

      <View style={styles.preview}>
        {trace ? <TracerOverlay points={trace.points} /> : <Text style={styles.placeholder}>Video preview</Text>}
      </View>

      <Pressable onPress={onMockTrack} style={styles.button}>
        <Text style={styles.buttonText}>Track Ball Flight</Text>
      </Pressable>

      {trace && (
        <View style={styles.metricsCard}>
          <Text style={styles.metric}>Shape: {trace.shotShape.toUpperCase()}</Text>
          <Text style={styles.metric}>Apex: {trace.apexHeightMeters.toFixed(1)} m</Text>
          <Text style={styles.metric}>Carry: {trace.estimatedCarryYards} yds</Text>
          <Text style={styles.metric}>Launch: {trace.launchDirectionDegrees.toFixed(1)}°</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: PremiumTheme.colors.background, padding: 20 },
  title: { fontSize: 32, color: PremiumTheme.colors.text, fontWeight: '700' },
  subtitle: { fontSize: 14, color: PremiumTheme.colors.muted, marginTop: 8, marginBottom: 18 },
  preview: {
    height: 380,
    backgroundColor: '#0F1622',
    borderRadius: PremiumTheme.radius.lg,
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholder: { color: PremiumTheme.colors.muted },
  button: {
    marginTop: 16,
    backgroundColor: PremiumTheme.colors.accent,
    borderRadius: PremiumTheme.radius.md,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonText: { color: '#021223', fontWeight: '700' },
  metricsCard: {
    marginTop: 16,
    padding: 14,
    borderRadius: PremiumTheme.radius.md,
    backgroundColor: PremiumTheme.colors.card,
    gap: 4,
  },
  metric: { color: PremiumTheme.colors.text, fontWeight: '600' },
});
