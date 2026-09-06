import { Stack } from 'expo-router';
import { RoleGate } from '../../src/management/navigation';
export default function AdminLayout() { return <RoleGate role="admin"><Stack screenOptions={{ headerShown: false }}><Stack.Screen name="(tabs)" /><Stack.Screen name="user" /><Stack.Screen name="branch" /><Stack.Screen name="product" /><Stack.Screen name="targets" /><Stack.Screen name="audit" /><Stack.Screen name="access" /><Stack.Screen name="reports" /><Stack.Screen name="help" /></Stack></RoleGate>; }
