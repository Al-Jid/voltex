import { useState } from 'react';
import { router } from 'expo-router';
import { Button, Card, Chips, Label, Pill, Progress, RowLink, Screen, useUI } from '../../components/ui';
import { useDemo } from '../../demo/DemoProvider';
export function RewardsScreen() {
  const { state } = useDemo(); const { tx } = useUI(); const points = state.sales.reduce((n, s) => n + s.quantity * 10, 0) + state.completedLessons.length * 20;
  return <Screen title={tx('Rewards', 'المكافآت')} subtitle={tx('Every achievement moves you forward', 'كل إنجاز بيقرّبك لهدفك')}>
    <Card tinted><Pill text={tx('RISING STAR', 'نجم صاعد')} /><Label size={40} bold>{points}</Label><Label muted>{tx('Demo points · 10 per unit + 20 per lesson', 'نقاط تجريبية · 10 لكل وحدة + 20 لكل درس')}</Label><Progress value={points / 500} /><Label size={12}>{Math.max(0, 500 - points)} {tx('points to your next milestone', 'نقطة للوصول للإنجاز التالي')}</Label></Card>
    <Label size={18} bold>{tx('Your badges', 'شاراتك')}</Label><Card><RowLink icon="star" title={tx('First sale', 'أول عملية بيع')} detail={tx('Your journey has started', 'رحلتك بدأت')} badge={tx('Earned', 'مكتسبة')} onPress={() => router.push('/(tabs)/sales')} /><RowLink icon="book" title={tx('Product expert', 'خبير المنتجات')} detail={tx('Complete both training lessons', 'أكمل درسي التدريب')} badge={state.completedLessons.length >= 2 ? tx('Earned', 'مكتسبة') : tx('In progress', 'قيد التقدم')} onPress={() => router.push('/detail/help')} /></Card>
    <Card><RowLink icon="reward" title={tx('The 10-unit challenge', 'تحدي العشر وحدات')} detail={tx('Build momentum, one conversation at a time', 'ابنِ نجاحك، محادثة بعد محادثة')} onPress={() => router.push('/detail/challenge')} /><Button title={state.joined ? tx('View your challenge', 'تابع تحديك') : tx('Explore challenge', 'استكشف التحدي')} onPress={() => router.push('/detail/challenge')} /></Card>
    <Card><RowLink icon="sales" title={tx('Team leaderboard', 'ترتيب الفريق')} detail={tx('Celebrate shared progress', 'احتفل بتقدم الفريق')} onPress={() => router.push('/detail/leaderboard')} /></Card>
  </Screen>;
}
export function ChallengeScreen() {
  const { state, update } = useDemo(); const { tx } = useUI(); const units = state.sales.reduce((n, s) => n + s.quantity, 0);
  return <Screen back title={tx('Challenge detail', 'تفاصيل التحدي')}>
    <Card tinted><Pill text={tx('SALES CHALLENGE', 'تحدي مبيعات')} /><Label bold size={29}>{tx('Ten units. One next level.', 'عشر وحدات. مستوى جديد.')}</Label><Label>{tx('A sample challenge to help you explore rewards.', 'تحدٍ تجريبي لاستكشاف نظام المكافآت.')}</Label></Card>
    <Card><Label bold>{tx('How it works', 'طريقة المشاركة')}</Label><Label>{tx('1. Join the challenge.\n2. Record 10 units in this demo workspace.\n3. Your progress updates automatically.', '1. انضم للتحدي.\n2. سجّل 10 وحدات في المساحة التجريبية.\n3. يتحدّث تقدمك تلقائيًا.')}</Label><Label muted>{tx('Existing sample sales count. Points are illustrative and cannot be redeemed.', 'تُحتسب المبيعات التجريبية الموجودة. النقاط توضيحية ولا يمكن استبدالها.')}</Label></Card>
    {state.joined && <Card><Label bold>{tx('Your progress', 'تقدمك')}: {Math.min(10, units)} / 10</Label><Progress value={units / 10} /><Pill text={units >= 10 ? tx('Challenge completed!', 'اكتمل التحدي!') : tx('Keep going', 'كمّل تقدمك')} /></Card>}
    <Button title={state.joined ? tx('Record your next sale', 'سجّل عمليتك القادمة') : tx('Join challenge', 'انضم للتحدي')} onPress={() => state.joined ? router.push('/sheet/log-sale') : update(s => ({ ...s, joined: true }))} />
  </Screen>;
}
export function LeaderboardScreen() {
  const { state } = useDemo(); const { tx } = useUI(); const [scope, setScope] = useState<'branch' | 'team'>('branch');
  const me = { name: state.profile.name, units: state.sales.reduce((n, s) => n + s.quantity, 0), me: true };
  const list = [...(scope === 'team' ? [{ name: 'Mariam Ali', units: 24 }, { name: 'Ahmed Adel', units: 18 }] : []), { name: 'Nour Samir', units: 12 }, { name: 'Omar Khaled', units: 8 }, me].sort((a, b) => b.units - a.units);
  return <Screen back title={tx('Leaderboard', 'لوحة الترتيب')} subtitle={tx('Illustrative team results', 'نتائج فريق توضيحية')}>
    <Chips value={scope} onChange={setScope} options={[{ value: 'branch', label: tx('My branch', 'فرعي') }, { value: 'team', label: tx('My team', 'فريقي') }]} />
    <Card tinted><Label bold size={25}>{tx('Grow together.', 'نكبر مع بعض.')}</Label><Label muted>{tx('Ranked by units in the demo workspace.', 'الترتيب حسب الوحدات في المساحة التجريبية.')}</Label></Card>
    {list.map((p, i) => <Card key={p.name} tinted={'me' in p}><Label bold size={19}>#{i + 1} · {p.name}{'me' in p ? tx(' (you)', ' (أنت)') : ''}</Label><Label muted>{p.units} {tx('units', 'وحدة')}</Label></Card>)}
  </Screen>;
}
