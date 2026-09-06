import { useEffect, useState } from 'react';
import { Switch, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Chips, Field, Label, Pill, Progress, RowLink, Screen, useUI } from '../../components/ui';
import { useDemo } from '../../demo/DemoProvider';
import { VoltexLogo } from '../../components/VoltexLogo';

export function MoreScreen() {
  const { tx, isDark } = useUI(); const { state } = useDemo();
  return <Screen title={tx('More', 'المزيد')} subtitle={tx('Everything for your workday', 'كل ما تحتاجه في يومك')}>
    <Card tinted><RowLink icon="user" title={state.profile.name} detail={tx('Promoter · Citystars', 'مروّج · سيتي ستارز')} onPress={() => router.push('/detail/profile')} /></Card>
    <Card><RowLink icon="clock" title={tx('Attendance', 'الحضور')} onPress={() => router.push('/detail/attendance')} /><RowLink icon="camera" title={tx('Shelf & photos', 'الأرفف والصور')} onPress={() => router.push('/detail/shelf')} /><RowLink icon="request" title={tx('Requests', 'الطلبات')} onPress={() => router.push('/detail/requests')} /><RowLink icon="bell" title={tx('Notifications', 'الإشعارات')} onPress={() => router.push('/detail/notifications')} /></Card>
    <Card><RowLink icon="settings" title={tx('Settings', 'الإعدادات')} detail={tx('Language, appearance & preferences', 'اللغة والمظهر والتفضيلات')} onPress={() => router.push('/detail/settings')} /><RowLink icon="book" title={tx('Help & training', 'المساعدة والتدريب')} onPress={() => router.push('/detail/help')} /></Card>
    <Button title={tx('Leave demo', 'الخروج من النسخة التجريبية')} secondary onPress={() => router.replace('/login')} /><View style={{ alignItems: 'center', paddingTop: 12 }}><VoltexLogo dark={isDark} /></View><Label muted size={11}>{tx('VOLTEX · Promoter workspace · v1.0', 'فولتكس · مساحة المروّج · الإصدار 1.0')}</Label>
  </Screen>;
}
export function ProfileScreen() {
  const { tx } = useUI(); const { state, update } = useDemo(); const [name, setName] = useState(state.profile.name); const [phone, setPhone] = useState(state.profile.phone); const [message, setMessage] = useState('');
  useEffect(() => { setName(state.profile.name); setPhone(state.profile.phone); }, [state.profile.name, state.profile.phone]);
  function save() { if (name.trim().length < 2 || (phone.trim() && !/^[+\d\s()-]{7,20}$/.test(phone))) { setMessage(tx('Enter a name and a valid phone number, or leave the phone blank.', 'أدخل اسمًا ورقم هاتف صحيحًا، أو اترك الهاتف فارغًا.')); return; } update(s => ({ ...s, profile: { name: name.trim(), phone: phone.trim() } })); setMessage(tx('Profile saved on this device.', 'تم حفظ الملف على الجهاز.')); }
  return <Screen back title={tx('My profile', 'ملفي الشخصي')}>
    <Card tinted><Pill text={tx('PROMOTER', 'مروّج')} /><Label bold size={27}>{state.profile.name}</Label><Label>{tx('Employee VX-024 · Demo identity', 'موظف VX-024 · هوية تجريبية')}</Label></Card>
    <Card><Label bold>{tx('Assignment', 'التكليف')}</Label><Label>{tx('Branch: Citystars, Nasr City', 'الفرع: سيتي ستارز، مدينة نصر')}</Label><Label>{tx('Supervisor: Ahmed Ali (sample)', 'المشرف: أحمد علي (تجريبي)')}</Label><Label muted size={12}>{tx('Role and branch assignments are managed by your supervisor.', 'المشرف هو المسؤول عن تعديل الدور وتكليفات الفروع.')}</Label></Card>
    <Field label={tx('Display name', 'الاسم الظاهر')} value={name} onChangeText={setName} maxLength={60} /><Field label={tx('Phone (optional, local demo only)', 'الهاتف (اختياري، محلي فقط)')} value={phone} onChangeText={setPhone} keyboardType="phone-pad" maxLength={20} />
    {!!message && <Label>{message}</Label>}<Button title={tx('Save profile', 'حفظ الملف')} onPress={save} />
  </Screen>;
}
export function SettingsScreen() {
  const { tx, mode, setMode, language, setLanguage, colors: c, row } = useUI(); const { state, update } = useDemo();
  return <Screen back title={tx('Settings', 'الإعدادات')} subtitle={tx('Make VOLTEX feel like you', 'فولتكس بالشكل اللي يناسبك')}>
    <Card><Label bold size={18}>{tx('Appearance', 'المظهر')}</Label><Chips value={mode} onChange={setMode} options={[{ value: 'light', label: tx('Light', 'فاتح') }, { value: 'dark', label: tx('Dark', 'داكن') }, { value: 'system', label: tx('System', 'حسب النظام') }]} /><Label muted size={12}>{tx('System follows your device appearance.', 'وضع النظام يتبع مظهر جهازك.')}</Label></Card>
    <Card><Label bold size={18}>{tx('Language', 'اللغة')}</Label><Chips value={language} onChange={setLanguage} options={[{ value: 'en', label: 'English' }, { value: 'ar', label: 'العربية' }]} /></Card>
    <Card><View style={[row, { alignItems: 'center', gap: 12 }]}><View style={{ flex: 1 }}><Label bold>{tx('Demo reminders', 'تذكيرات تجريبية')}</Label><Label muted size={12}>{tx('Show sample challenge and training reminders', 'إظهار تذكيرات التحدي والتدريب التجريبية')}</Label></View><Switch accessibilityLabel={tx('Demo reminders', 'تذكيرات تجريبية')} value={state.notifications} onValueChange={notifications => update(s => ({ ...s, notifications }))} trackColor={{ false: c.circle, true: c.primary }} /></View></Card>
    <Card><Label bold>{tx('Your data', 'بياناتك')}</Label><Label muted>{tx('Demo records are stored on this device. No server sync or push notifications are active.', 'السجلات التجريبية محفوظة على الجهاز. لا توجد مزامنة مع الخادم أو إشعارات دفع مفعلة.')}</Label><Label muted>{tx('Biometric sign-in becomes available after secure account integration.', 'يتاح الدخول بالبصمة بعد ربط الحسابات الآمنة.')}</Label></Card>
    <Button title={tx('Replay introduction', 'عرض المقدمة مجددًا')} secondary onPress={() => router.push('/onboarding')} />
  </Screen>;
}
export function NotificationsScreen() {
  const { tx } = useUI(); const { state, update } = useDemo(); const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const items = [
    ...state.requests.filter(r => r.status === 'pending').map(r => ({ id: r.id, title: tx('Request saved locally', 'تم حفظ الطلب محليًا'), body: tx('Your request is ready for future supervisor review.', 'طلبك جاهز لمراجعة المشرف بعد الربط.'), open: () => router.push({ pathname: '/detail/request', params: { id: r.id } }) })),
    ...(state.notifications ? [{ id: 'challenge', title: tx('Your next challenge awaits', 'تحديك القادم في انتظارك'), body: tx('Explore the 10-unit challenge.', 'استكشف تحدي العشر وحدات.'), open: () => router.push('/detail/challenge') }, { id: 'training', title: tx('Know your products', 'اعرف منتجاتك'), body: tx('Two short guides for a stronger workday.', 'دليلان مختصران ليوم عمل أفضل.'), open: () => router.push('/detail/help') }] : []),
  ]; const list = items.filter(n => filter === 'all' || !state.readNotifications.includes(n.id));
  return <Screen back title={tx('Notifications', 'الإشعارات')} subtitle={tx('Updates that matter to your day', 'تحديثات تهم يومك')}>
    <Chips value={filter} onChange={setFilter} options={[{ value: 'all', label: tx('All', 'الكل') }, { value: 'unread', label: tx('Unread', 'غير مقروء') }]} />
    <Button title={tx('Mark all as read', 'تحديد الكل كمقروء')} secondary disabled={items.every(n => state.readNotifications.includes(n.id))} onPress={() => update(s => ({ ...s, readNotifications: [...new Set([...s.readNotifications, ...items.map(n => n.id)])] }))} />
    {!list.length && <Card><Label bold>{tx('You’re all caught up', 'اطلعت على كل جديد')}</Label><Label muted>{tx('Nothing new in this view.', 'لا يوجد جديد في هذا العرض.')}</Label></Card>}
    {list.map(n => <Card key={n.id}><Pill text={state.readNotifications.includes(n.id) ? tx('Read', 'مقروء') : tx('New', 'جديد')} /><RowLink icon="bell" title={n.title} detail={n.body} onPress={() => { update(s => ({ ...s, readNotifications: [...new Set([...s.readNotifications, n.id])] })); n.open(); }} /></Card>)}
  </Screen>;
}
export function HelpScreen() {
  const { tx } = useUI(); const { state, update } = useDemo(); const [open, setOpen] = useState<string | null>(null);
  const lessons = [
    { id: 'sales', title: tx('A better product conversation', 'محادثة أفضل مع العميل'), body: tx('1. Ask what the customer needs and their budget.\n2. Compare the listed product specifications, not assumptions.\n3. Confirm the current branch price and availability.\n4. Explain warranty terms using approved material.\n5. Record the correct product and quantity after the sale.', '1. اسأل عن احتياج العميل وميزانيته.\n2. قارن المواصفات المعتمدة دون تخمين.\n3. تأكد من سعر الفرع والتوافر الحالي.\n4. وضّح الضمان من المواد المعتمدة.\n5. سجّل المنتج والكمية الصحيحين بعد البيع.') },
    { id: 'shelf', title: tx('The shelf photo checklist', 'قائمة مراجعة صورة الرف'), body: tx('1. Include the full display in the frame.\n2. Keep prices and product labels readable.\n3. Avoid glare and motion blur.\n4. Keep customers and personal information out of frame.\n5. Review your photo before saving and explain any issues in the notes.', '1. أظهر العرض كاملًا داخل الإطار.\n2. تأكد من وضوح الأسعار وأسماء المنتجات.\n3. تجنّب الانعكاسات واهتزاز الصورة.\n4. أبعد العملاء والمعلومات الشخصية عن الإطار.\n5. راجع الصورة قبل الحفظ ووضّح المشاكل في الملاحظات.') },
  ];
  return <Screen back title={tx('Help & training', 'المساعدة والتدريب')} subtitle={tx('A little knowledge goes a long way', 'المعرفة الصغيرة تصنع فرقًا كبيرًا')}>
    <Card tinted><Label bold size={24}>{state.completedLessons.length} / 2 {tx('lessons complete', 'دروس مكتملة')}</Label><Progress value={state.completedLessons.length / 2} /></Card>
    {lessons.map(l => <Card key={l.id}><RowLink icon="book" title={l.title} detail={tx('2 min read', 'قراءة دقيقتين')} badge={state.completedLessons.includes(l.id) ? tx('Done', 'مكتمل') : undefined} onPress={() => setOpen(open === l.id ? null : l.id)} />{open === l.id && <><Label>{l.body}</Label><Button title={state.completedLessons.includes(l.id) ? tx('Completed', 'مكتمل') : tx('Mark as complete', 'تحديد كمكتمل')} disabled={state.completedLessons.includes(l.id)} onPress={() => update(s => ({ ...s, completedLessons: [...new Set([...s.completedLessons, l.id])] }))} /></>}</Card>)}
    <Card><Label bold size={18}>{tx('Quick answers', 'إجابات سريعة')}</Label><Label bold>{tx('Where are my records?', 'أين توجد سجلاتي؟')}</Label><Label muted>{tx('They are saved locally in this demo, not sent to your supervisor.', 'محفوظة محليًا في هذه النسخة، ولم تُرسل إلى المشرف.')}</Label><Label bold>{tx('How do I get an account?', 'كيف أحصل على حساب؟')}</Label><Label muted>{tx('Your supervisor will create or invite your account when services are connected.', 'سيُنشئ المشرف حسابك أو يرسل دعوة عند ربط الخدمات.')}</Label></Card>
  </Screen>;
}
export function ForgotPasswordScreen() {
  const { tx } = useUI(); const [username, setUsername] = useState(''); const [error, setError] = useState(''); const [requested, setRequested] = useState(false);
  return <Screen back title={tx('Forgot password?', 'نسيت كلمة المرور؟')} subtitle={tx('Let’s get you back on track', 'نساعدك ترجع لحسابك')}>
    <Card tinted><Label bold size={22}>{tx('Restore account access', 'استعادة الوصول للحساب')}</Label><Label>{tx('Enter your username to prepare a recovery request.', 'أدخل اسم المستخدم لتجهيز طلب الاستعادة.')}</Label></Card>
    <Field label={tx('Username', 'اسم المستخدم')} value={username} autoCapitalize="none" autoCorrect={false} onChangeText={v => { setUsername(v); setRequested(false); setError(''); }} error={error} />
    {requested && <Card><Label bold>{tx('Recovery preview', 'معاينة الاستعادة')}</Label><Label>{tx('No request was sent. Contact your supervisor for account help until recovery services are connected.', 'لم يُرسل أي طلب. تواصل مع المشرف للمساعدة حتى يتم ربط خدمة الاستعادة.')}</Label></Card>}
    <Button title={tx('Continue', 'متابعة')} onPress={() => { if (!username.trim()) setError(tx('Enter your username.', 'أدخل اسم المستخدم.')); else setRequested(true); }} />
    <Button title={tx('Back to login', 'العودة لتسجيل الدخول')} secondary onPress={() => router.replace('/login')} />
  </Screen>;
}
