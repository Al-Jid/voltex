import { Pressable, Text, View, useColorScheme } from 'react-native';
import type { ErrorBoundaryProps } from 'expo-router';

/** Independent of app providers so storage/theme failures can also be recovered. */
export function AppErrorBoundary({ retry }: ErrorBoundaryProps) {
  const dark = useColorScheme() === 'dark';
  return <View style={{ flex: 1, justifyContent: 'center', padding: 28, gap: 18, backgroundColor: dark ? '#14121C' : '#FFFAFF' }}>
    <Text accessibilityRole="header" style={{ color: dark ? '#F5F1FC' : '#202024', fontSize: 24, fontWeight: '700' }}>Let’s try that again{'\n'}خلّينا نحاول تاني</Text>
    <Text style={{ color: dark ? '#C0B8CF' : '#53505C', fontSize: 15, lineHeight: 24 }}>This screen couldn’t load. Retry to reopen your workspace.{'\n'}تعذّر تحميل الشاشة. أعد المحاولة لفتح مساحة العمل.</Text>
    <Pressable accessibilityRole="button" onPress={() => void retry()} style={{ minHeight: 48, borderRadius: 9, backgroundColor: '#4D3BC1', alignItems: 'center', justifyContent: 'center' }}><Text style={{ color: '#FFFFFF', fontSize: 15 }}>Try again · إعادة المحاولة</Text></Pressable>
  </View>;
}
