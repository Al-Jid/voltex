import { useEffect, useState } from 'react';
import { ScrollView, View, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from 'expo-router';
import { VoltexLogo } from '../../components/VoltexLogo';
import { AppIcon, type AppIconName } from '../../components/AppIcon';
import { Button, Label, useUI } from '../../components/ui';
const KEY = '@voltex/onboarded';
export function SplashScreen() {
  const { colors: c, isDark, tx } = useUI();
  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => { void AsyncStorage.getItem(KEY).then(seen => { if (active) router.replace(seen ? '/login' : '/onboarding'); }).catch(() => { if (active) router.replace('/onboarding'); }); }, 900);
    return () => { active = false; clearTimeout(timer); };
  }, []);
  return <SafeAreaView style={{ flex: 1, backgroundColor: c.background, alignItems: 'center', justifyContent: 'center', gap: 20 }}><VoltexLogo dark={isDark} /><Label muted>{tx('Powering your every day.', 'قوة تدفع يومك للأفضل.')}</Label></SafeAreaView>;
}
export function OnboardingScreen() {
  const { colors: c, isDark, tx } = useUI(); const [page, setPage] = useState(0);
  const slides: { icon: AppIconName; title: string; body: string }[] = [
    { icon: 'sales', title: tx('Your effort. Your impact.', 'مجهودك يصنع الفرق.'), body: tx('Log sales in seconds and keep your daily target in sight.', 'سجّل مبيعاتك في ثوانٍ وتابع تقدمك نحو مستهدفك اليومي.') },
    { icon: 'stock', title: tx('Every shelf matters.', 'كل رف له قيمة.'), body: tx('Track availability, capture your display and request what your branch needs.', 'تابع توافر المنتجات وصوّر العرض واطلب احتياجات فرعك.') },
    { icon: 'reward', title: tx('Make progress count.', 'خلّي إنجازك يستحق.'), body: tx('Build your skills, join challenges and celebrate your achievements.', 'طوّر مهاراتك وشارك في التحديات واحتفل بإنجازاتك.') },
  ]; const slide = slides[page]!;
  async function finish() { try { await AsyncStorage.setItem(KEY, 'yes'); } catch {} router.replace('/login'); }
  return <SafeAreaView style={{ flex: 1, backgroundColor: c.background }}><ScrollView contentContainerStyle={{ flexGrow: 1, padding: 24, gap: 24, width: '100%', maxWidth: 600, alignSelf: 'center' }}>
    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}><VoltexLogo dark={isDark} /><Button title={tx('Skip', 'تخطي')} secondary onPress={() => void finish()} /></View>
    <View style={{ flexGrow: 1, alignItems: 'center', justifyContent: 'center', gap: 28, paddingVertical: 16 }}>
      <View style={{ width: 220, height: 220, borderRadius: 110, backgroundColor: c.notice, alignItems: 'center', justifyContent: 'center' }}><View style={{ width: 145, height: 145, backgroundColor: c.surface, borderRadius: 42, alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '-7deg' }] }}><AppIcon name={slide.icon} size={72} color={c.primary} /></View></View>
      <Text style={{ fontSize: 29, fontWeight: '700', color: c.text, textAlign: 'center' }}>{slide.title}</Text><Text style={{ color: c.muted, fontSize: 16, lineHeight: 25, textAlign: 'center', maxWidth: 360 }}>{slide.body}</Text>
      <View style={{ flexDirection: 'row', gap: 6 }}>{slides.map((_, i) => <View key={i} style={{ width: page === i ? 26 : 7, height: 7, borderRadius: 5, backgroundColor: page === i ? c.primary : c.notice }} />)}</View>
    </View>
    <Button title={page === 2 ? tx('Get started', 'ابدأ الآن') : tx('Next', 'التالي')} onPress={() => page === 2 ? void finish() : setPage(page + 1)} />
    {page > 0 && <View style={{ marginTop: 10 }}><Button title={tx('Back', 'السابق')} secondary onPress={() => setPage(page - 1)} /></View>}
  </ScrollView></SafeAreaView>;
}
