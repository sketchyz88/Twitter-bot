import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { PremiumTheme } from '@/theme/premiumTheme';

export function SettingsScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Creator Settings</Text>
      <Text style={styles.item}>• Overlay style presets</Text>
      <Text style={styles.item}>• Watermark username</Text>
      <Text style={styles.item}>• Vertical export default</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: PremiumTheme.colors.background, padding: 20 },
  title: { color: PremiumTheme.colors.text, fontSize: 28, fontWeight: '700', marginBottom: 12 },
  item: { color: PremiumTheme.colors.muted, marginTop: 8 },
});
