import type { PropsWithChildren } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, type TextInputProps, type ViewStyle } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { usePreferences } from '../theme/Preferences';
import { useDemo } from '../demo/DemoProvider';
import { AppIcon, type AppIconName } from './AppIcon';

export function useUI() {
  const p = usePreferences();
  return { ...p, tx: (en: string, ar: string) => p.language === 'ar' ? ar : en,
    row: { flexDirection: p.language === 'ar' ? 'row-reverse' : 'row' } as ViewStyle,
    money: (amount: number) => new Intl.NumberFormat(p.language === 'ar' ? 'ar-EG' : 'en-EG', { style: 'currency', currency: 'EGP', maximumFractionDigits: 0 }).format(amount),
    date: (value: string) => new Date(value).toLocaleString(p.language === 'ar' ? 'ar-EG' : 'en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }),
  };
}
export function Label({ children, muted, size = 14, bold = false }: PropsWithChildren<{ muted?: boolean; size?: number; bold?: boolean }>) {
  const { colors: c, language } = useUI();
  return <Text style={{ color: muted ? c.muted : c.text, fontSize: size, lineHeight: size * 1.45, fontWeight: bold ? '700' : '400', textAlign: language === 'ar' ? 'right' : 'left', writingDirection: language === 'ar' ? 'rtl' : 'ltr' }}>{children}</Text>;
}
export function Screen({ title, subtitle, children, back = false, action }: PropsWithChildren<{ title: string; subtitle?: string; back?: boolean; action?: { icon: AppIconName; label: string; run: () => void } }>) {
  const { colors: c, row, tx, isDark } = useUI(); const { ready, storageError } = useDemo(); const insets = useSafeAreaInsets();
  return <SafeAreaView edges={['top', 'left', 'right']} style={{ flex: 1, backgroundColor: c.background }}>
    <StatusBar style={isDark ? 'light' : 'dark'} />
    <View style={[s.header, row]}>{back && <IconButton name="back" label={tx('Back', 'رجوع')} onPress={() => router.canGoBack() ? router.back() : router.replace('/(tabs)/home')} />}
      <View style={{ flex: 1 }}><Label size={24} bold>{title}</Label>{subtitle && <Label muted size={12}>{subtitle}</Label>}</View>
      {action && <IconButton name={action.icon} label={action.label} onPress={action.run} />}
    </View>
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[s.content, { paddingBottom: 100 + insets.bottom }]}>
        <View style={{ backgroundColor: c.notice, padding: 8, borderRadius: 8 }}><Label size={11}>{storageError ? tx('Storage unavailable · changes may not survive restart', 'التخزين غير متاح · قد لا تُحفظ التغييرات بعد الإغلاق') : tx('Demo workspace · data stays on this device', 'مساحة تجريبية · البيانات على هذا الجهاز فقط')}</Label></View>
        {ready ? children : <Label>{tx('Loading local workspace…', 'جارٍ تحميل البيانات المحلية…')}</Label>}
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
export function Card({ children, tinted = false }: PropsWithChildren<{ tinted?: boolean }>) { const { colors: c } = useUI(); return <View style={[s.card, { backgroundColor: tinted ? c.notice : c.surface, borderColor: c.border + '35' }]}>{children}</View>; }
export function Button({ title, onPress, secondary = false, disabled = false }: { title: string; onPress: () => void; secondary?: boolean; disabled?: boolean }) { const { colors: c } = useUI(); return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={onPress} style={({ pressed }) => [s.button, { backgroundColor: secondary ? c.notice : c.primary, opacity: disabled ? 0.4 : pressed ? 0.7 : 1 }]}><Text style={{ color: secondary ? c.primary : c.onPrimary, fontSize: 14, fontWeight: '600', textAlign: 'center' }}>{title}</Text></Pressable>; }
export function IconButton({ name, label, onPress }: { name: AppIconName; label: string; onPress: () => void }) { const { colors: c, language } = useUI(); return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={({ pressed }) => ({ minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', opacity: pressed ? 0.5 : 1, transform: [{ scaleX: name === 'back' && language === 'ar' ? -1 : 1 }] })}><AppIcon name={name} color={c.primary} /></Pressable>; }
export function RowLink({ title, detail, icon = 'next', onPress, badge }: { title: string; detail?: string; icon?: AppIconName; onPress: () => void; badge?: string }) { const { colors: c, row, language } = useUI(); return <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [s.link, row, { opacity: pressed ? 0.6 : 1 }]}><View style={[s.iconTile, { backgroundColor: c.notice }]}><AppIcon name={icon} color={c.primary} /></View><View style={{ flex: 1, gap: 3 }}><Label bold>{title}</Label>{detail && <Label size={12} muted>{detail}</Label>}</View>{badge && <Pill text={badge} />}<AppIcon name={language === 'ar' ? 'back' : 'next'} color={c.muted} size={17} /></Pressable>; }
export function Pill({ text }: { text: string }) { const { colors: c } = useUI(); return <View style={{ backgroundColor: c.notice, alignSelf: 'flex-start', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 20 }}><Text style={{ fontSize: 11, color: c.primary, fontWeight: '600' }}>{text}</Text></View>; }
export function Field({ label, error, ...props }: TextInputProps & { label: string; error?: string }) { const { colors: c, language } = useUI(); return <View style={{ gap: 6 }}><Label size={12} bold>{label}</Label><TextInput accessibilityLabel={label} placeholderTextColor={c.muted} {...props} style={[s.input, { color: c.text, borderColor: error ? c.error : c.border, backgroundColor: c.field, textAlign: language === 'ar' ? 'right' : 'left', minHeight: props.multiline ? 90 : 48 }, props.style]} />{error && <Text accessibilityLiveRegion="polite" style={{ color: c.error, fontSize: 12 }}>{error}</Text>}</View>; }
export function Chips<T extends string>({ options, value, onChange }: { options: { value: T; label: string }[]; value: T; onChange: (value: T) => void }) { const { colors: c, row } = useUI(); return <View style={[row, { flexWrap: 'wrap', gap: 8 }]}>{options.map(o => <Pressable key={o.value} accessibilityRole="radio" accessibilityState={{ checked: value === o.value }} onPress={() => onChange(o.value)} style={{ minHeight: 44, paddingHorizontal: 14, paddingVertical: 12, borderRadius: 10, backgroundColor: value === o.value ? c.primary : c.circle }}><Text style={{ color: value === o.value ? c.onPrimary : c.muted, fontSize: 12, fontWeight: '600' }}>{o.label}</Text></Pressable>)}</View>; }
export function Progress({ value }: { value: number }) { const { colors: c } = useUI(); return <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: 100, now: Math.round(value * 100) }} style={{ height: 7, backgroundColor: c.circle, borderRadius: 4, overflow: 'hidden' }}><View style={{ width: `${Math.max(0, Math.min(100, value * 100))}%`, height: 7, backgroundColor: c.primary, borderRadius: 4 }} /></View>; }
export function Empty({ title, detail }: { title: string; detail: string }) { return <Card><Label bold size={17}>{title}</Label><Label muted>{detail}</Label></Card>; }
export const s = StyleSheet.create({ header: { padding: 20, gap: 8, alignItems: 'center', width: '100%', maxWidth: 680, alignSelf: 'center' }, content: { padding: 20, paddingTop: 0, paddingBottom: 42, gap: 16, width: '100%', maxWidth: 680, alignSelf: 'center' }, card: { padding: 18, borderRadius: 16, borderWidth: 1, gap: 12 }, button: { minHeight: 48, justifyContent: 'center', borderRadius: 9, padding: 12 }, link: { minHeight: 65, alignItems: 'center', gap: 12, paddingVertical: 6 }, iconTile: { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center' }, input: { borderWidth: 0.8, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 12, fontSize: 14 } });
