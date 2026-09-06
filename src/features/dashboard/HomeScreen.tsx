import { View } from 'react-native';
import { router } from 'expo-router';
import { Screen, Card, Label, Button, RowLink, Progress, Pill, useUI } from '../../components/ui';
import { useDemo, products } from '../../demo/DemoProvider';
export function HomeScreen() {
  const { tx, money, row } = useUI(); const { state } = useDemo();
  const today = state.sales.filter(s => new Date(s.date).toDateString() === new Date().toDateString());
  const total = today.reduce((n, s) => n + (products.find(p => p.id === s.productId)?.price ?? 0) * s.quantity, 0);
  const active = state.shifts.find(s => !s.end);
  return <Screen title={tx('Hello, ' + state.profile.name.split(' ')[0], 'أهلًا، ' + state.profile.name.split(' ')[0])} subtitle={tx('Citystars · Nasr City', 'سيتي ستارز · مدينة نصر')} action={{ icon: 'bell', label: tx('Notifications', 'الإشعارات'), run: () => router.push('/detail/notifications') }}>
    <Card tinted><Pill text={tx('YOUR DAY, AT A GLANCE', 'يومك في لمحة')} /><Label size={32} bold>{money(total)}</Label><Label muted>{tx('Sales today · target EGP 75,000', 'مبيعات اليوم · المستهدف 75,000 جنيه')}</Label><Progress value={total / 75000} /><View style={[row, { justifyContent: 'space-between' }]}><Label size={12}>{Math.round(total / 750)}% {tx('of target', 'من المستهدف')}</Label><Label size={12}>{today.reduce((n, s) => n + s.quantity, 0)} {tx('units sold', 'وحدة مباعة')}</Label></View><Button title={tx('+ Log a sale', '+ تسجيل بيع')} onPress={() => router.push('/sheet/log-sale')} /></Card>
    <Card><RowLink icon="clock" title={active ? tx('You’re checked in', 'تم تسجيل حضورك') : tx('Ready to start your shift?', 'جاهز تبدأ ورديتك؟')} detail={tx('Attendance · Citystars branch', 'الحضور · فرع سيتي ستارز')} onPress={() => router.push('/detail/attendance')} /></Card>
    <Label bold size={18}>{tx('Your next actions', 'خطواتك التالية')}</Label>
    <Card><RowLink icon="stock" title={tx('2 products need attention', 'منتجان يحتاجان متابعة')} detail={tx('Review low and out-of-stock products', 'راجع المنتجات الناقصة والمنتهية')} onPress={() => router.push('/(tabs)/stock')} /><RowLink icon="camera" title={tx('Make your display stand out', 'خلّي عرضك مميز')} detail={tx('Capture shelf photos for review', 'صوّر الأرفف للمراجعة')} onPress={() => router.push('/detail/shelf')} /><RowLink icon="request" title={tx('Track your requests', 'تابع طلباتك')} detail={`${state.requests.filter(r => r.status === 'pending').length} ${tx('awaiting review', 'في انتظار المراجعة')}`} onPress={() => router.push('/detail/requests')} /></Card>
    <Card tinted><Label bold size={18}>{tx('A little learning. A bigger impact.', 'تعلّم بسيط. تأثير أكبر.')}</Label><Label muted>{tx('Get to know your products before your next conversation.', 'اعرف منتجاتك قبل محادثتك القادمة مع العميل.')}</Label><Button title={tx('Open training', 'افتح التدريب')} secondary onPress={() => router.push('/detail/help')} /></Card>
  </Screen>;
}
