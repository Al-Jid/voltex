import { Stack } from 'expo-router';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PreferencesProvider } from '../src/theme/Preferences';
import { DemoProvider } from '../src/demo/DemoProvider';
import { ManagementProvider } from '../src/management/ManagementProvider';
export { AppErrorBoundary as ErrorBoundary } from '../src/components/AppErrorBoundary';

export default function RootLayout() {
  return <SafeAreaProvider><PreferencesProvider><DemoProvider><ManagementProvider><Stack initialRouteName="index" screenOptions={{ headerShown: false }}>
    <Stack.Screen name="index" /><Stack.Screen name="onboarding" /><Stack.Screen name="login" />
    <Stack.Screen name="(tabs)" />
    <Stack.Screen name="demo-role" /><Stack.Screen name="supervisor" /><Stack.Screen name="admin" />
    <Stack.Screen name="detail/sale" />
    <Stack.Screen name="detail/challenge" />
    <Stack.Screen name="detail/leaderboard" />
    <Stack.Screen name="detail/attendance" />
    <Stack.Screen name="detail/attendance-log" />
    <Stack.Screen name="detail/requests" />
    <Stack.Screen name="detail/request" />
    <Stack.Screen name="detail/shelf" />
    <Stack.Screen name="detail/profile" />
    <Stack.Screen name="detail/settings" />
    <Stack.Screen name="detail/notifications" />
    <Stack.Screen name="detail/help" />
    <Stack.Screen name="sheet/log-sale" options={{ presentation: 'modal' }} />
    <Stack.Screen name="sheet/submit-count" options={{ presentation: 'modal' }} />
    <Stack.Screen name="sheet/new-request" options={{ presentation: 'modal' }} />
    <Stack.Screen name="sheet/capture-photo" options={{ presentation: 'modal' }} />
    <Stack.Screen name="sheet/forgot-password" options={{ presentation: 'modal' }} />
  </Stack></ManagementProvider></DemoProvider></PreferencesProvider></SafeAreaProvider>;
}
