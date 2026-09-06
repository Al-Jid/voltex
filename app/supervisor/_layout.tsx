import { Stack } from 'expo-router';
import { RoleGate } from '../../src/management/navigation';
export default function SupervisorLayout() { return <RoleGate role="supervisor"><Stack screenOptions={{ headerShown: false }}><Stack.Screen name="(tabs)" /><Stack.Screen name="member" /><Stack.Screen name="review" /><Stack.Screen name="help" /><Stack.Screen name="task" options={{ presentation: 'modal' }} /></Stack></RoleGate>; }
