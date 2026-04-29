import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { PremiumTheme } from '@/theme/premiumTheme';

export function LibraryScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Shot Library</Text>
      <Text style={styles.body}>Organize by club, favorite key swings, and export social-ready clips.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: PremiumTheme.colors.background, padding: 20 },
  title: { color: PremiumTheme.colors.text, fontSize: 28, fontWeight: '700' },
  body: { color: PremiumTheme.colors.muted, marginTop: 10 },
});
