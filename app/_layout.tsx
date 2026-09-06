import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PreferencesProvider } from '../src/theme/Preferences';
import { DemoProvider } from '../src/demo/DemoProvider';

export default function RootLayout() {
  return <SafeAreaProvider><PreferencesProvider><DemoProvider><Stack screenOptions={{ headerShown: false }}>
    <Stack.Screen name="index" /><Stack.Screen name="onboarding" /><Stack.Screen name="login" />
    <Stack.Screen name="(tabs)" /><Stack.Screen name="detail/[screen]" />
    <Stack.Screen name="sheet/[screen]" options={{ presentation: 'modal' }} />
  </Stack></DemoProvider></PreferencesProvider></SafeAreaProvider>;
}
