import type { PropsWithChildren } from 'react';
import { Redirect, router, useIsFocused } from 'expo-router';
import { Tabs } from 'expo-router/js-tabs';
import { AppIcon, type AppIconName } from '../components/AppIcon';
import { Button, Card, Label, Screen, useUI } from '../components/ui';
import { useManagement, type Role } from './ManagementProvider';

export function RoleGate({ role, children }: PropsWithChildren<{ role: Role }>) {
  const m = useManagement(); const { tx } = useUI(); const focused = useIsFocused();
  if (m.role !== role) return focused ? <Redirect href="/demo-role" /> : null;
  if (!m.ready) return <Screen title={tx('Loading workspace…', 'جارٍ تحميل مساحة العمل…')} />;
  return <>{children}</>;
}
export function ManagementTabs({ role }: { role: 'admin' | 'supervisor' }) {
  const { colors: c, tx } = useUI();
  const tabs: { name: string; label: string; icon: AppIconName }[] = role === 'admin'
    ? [{ name: 'home', label: tx('Overview', 'نظرة عامة'), icon: 'home' }, { name: 'users', label: tx('Users', 'الحسابات'), icon: 'user' }, { name: 'branches', label: tx('Branches', 'الفروع'), icon: 'pin' }, { name: 'catalog', label: tx('Catalog', 'الكتالوج'), icon: 'stock' }, { name: 'more', label: tx('More', 'المزيد'), icon: 'more' }]
    : [{ name: 'home', label: tx('Overview', 'نظرة عامة'), icon: 'home' }, { name: 'team', label: tx('Team', 'الفريق'), icon: 'user' }, { name: 'reviews', label: tx('Reviews', 'المراجعات'), icon: 'check' }, { name: 'reports', label: tx('Reports', 'التقارير'), icon: 'sales' }, { name: 'more', label: tx('More', 'المزيد'), icon: 'more' }];
  return <Tabs screenOptions={{ headerShown: false, tabBarActiveTintColor: c.primary, tabBarInactiveTintColor: c.muted, tabBarStyle: { backgroundColor: c.surface, borderTopColor: c.border + '40' }, tabBarLabelStyle: { fontSize: 10 }, tabBarHideOnKeyboard: true }}>{tabs.map(t => <Tabs.Screen key={t.name} name={t.name} options={{ title: t.label, tabBarIcon: ({ color }) => <AppIcon name={t.icon} color={color} /> }} />)}</Tabs>;
}
export function ManagementNotice() { const { storageError } = useManagement(); const { tx } = useUI(); return storageError ? <Card><Label>{tx('Management storage unavailable. Changes may remain in memory only.', 'التخزين الإداري غير متاح. قد تبقى التغييرات في الذاكرة فقط.')}</Label></Card> : null; }
export function RolePicker() {
  const { setRole } = useManagement(); const { tx } = useUI();
  const options: { role: Role; title: string; body: string; path: '/(tabs)/home' | '/supervisor/home' | '/admin/home' }[] = [
    { role: 'promoter', title: tx('Promoter', 'المروّج'), body: tx('Sales, attendance, stock and your daily progress.', 'المبيعات والحضور والمخزون وتقدمك اليومي.'), path: '/(tabs)/home' },
    { role: 'supervisor', title: tx('Supervisor', 'المشرف'), body: tx('Your team, field activity, reviews and tasks.', 'فريقك والنشاط الميداني والمراجعات والمهام.'), path: '/supervisor/home' },
    { role: 'admin', title: tx('Admin', 'مدير النظام'), body: tx('Accounts, branches, catalog, targets and audit history.', 'الحسابات والفروع والكتالوج والمستهدفات وسجل التغييرات.'), path: '/admin/home' },
  ];
  return <Screen back title={tx('Explore VOLTEX', 'استكشف فولتكس')} subtitle={tx('Choose a demo workspace', 'اختر مساحة تجريبية')}><Card tinted><Label>{tx('These are local demo identities. Real account roles will be assigned by the server after sign-in.', 'هذه هويات تجريبية محلية. الدور الحقيقي سيحدده الخادم بعد تسجيل الدخول.')}</Label></Card>{options.map(o => <Card key={o.role}><Label bold size={23}>{o.title}</Label><Label muted>{o.body}</Label><Button title={tx('Explore', 'استكشاف')} onPress={() => { setRole(o.role); router.replace(o.path); }} /></Card>)}</Screen>;
}
