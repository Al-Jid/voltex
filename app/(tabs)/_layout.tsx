import { router } from 'expo-router';
import { Tabs } from 'expo-router/js-tabs';
import { Keyboard, Pressable, View } from 'react-native';
import { useEffect, useState } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AppIcon } from '../../src/components/AppIcon';
import { useUI } from '../../src/components/ui';
export default function TabsLayout() {
  const { colors: c, tx, language } = useUI(); const insets = useSafeAreaInsets(); const [keyboard, setKeyboard] = useState(false);
  useEffect(() => { const show = Keyboard.addListener('keyboardDidShow', () => setKeyboard(true)); const hide = Keyboard.addListener('keyboardDidHide', () => setKeyboard(false)); return () => { show.remove(); hide.remove(); }; }, []);
  return <View style={{ flex: 1 }}><Tabs screenOptions={{ headerShown: false, tabBarActiveTintColor: c.primary, tabBarInactiveTintColor: c.muted, tabBarStyle: { backgroundColor: c.surface, borderTopColor: c.border + '40' }, tabBarLabelStyle: { fontSize: 10 }, tabBarHideOnKeyboard: true }}>
    <Tabs.Screen name="home" options={{ title: tx('Home', 'الرئيسية'), tabBarIcon: ({ color }) => <AppIcon name="home" color={color} /> }} />
    <Tabs.Screen name="sales" options={{ title: tx('Sales', 'المبيعات'), tabBarIcon: ({ color }) => <AppIcon name="sales" color={color} /> }} />
    <Tabs.Screen name="stock" options={{ title: tx('Stock', 'المخزون'), tabBarIcon: ({ color }) => <AppIcon name="stock" color={color} /> }} />
    <Tabs.Screen name="rewards" options={{ title: tx('Rewards', 'المكافآت'), tabBarIcon: ({ color }) => <AppIcon name="reward" color={color} /> }} />
    <Tabs.Screen name="more" options={{ title: tx('More', 'المزيد'), tabBarIcon: ({ color }) => <AppIcon name="more" color={color} /> }} />
  </Tabs>{!keyboard && <Pressable accessibilityRole="button" accessibilityLabel={tx('Quick add sale', 'تسجيل بيع سريع')} onPress={() => router.push('/sheet/log-sale')} style={({ pressed }) => ({ position: 'absolute', bottom: 68 + insets.bottom, right: language === 'ar' ? undefined : 20, left: language === 'ar' ? 20 : undefined, width: 54, height: 54, borderRadius: 18, backgroundColor: c.primary, alignItems: 'center', justifyContent: 'center', opacity: pressed ? 0.7 : 1, elevation: 5, shadowColor: '#25145F', shadowOpacity: 0.18, shadowRadius: 9, shadowOffset: { width: 0, height: 4 } })}><AppIcon name="plus" color={c.onPrimary} size={26} /></Pressable>}</View>;
}
