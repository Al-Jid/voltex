import { Alert } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Empty, Label, Pill, RowLink, Screen, useUI } from '../../components/ui';
import { makeId, useDemo } from '../../demo/DemoProvider';
export function AttendanceScreen() {
  const { tx, date } = useUI(); const { state, update } = useDemo(); const active = state.shifts.find(s => !s.end);
  function toggle() {
    Alert.alert(active ? tx('End this shift?', 'إنهاء الوردية؟') : tx('Start a demo shift?', 'بدء وردية تجريبية؟'), tx('This records a local timestamp only. Location and attendance are not verified.', 'سيُسجّل توقيت محلي فقط. لم يتم التحقق من الموقع أو الحضور.'), [
      { text: tx('Cancel', 'إلغاء'), style: 'cancel' }, { text: tx('Confirm', 'تأكيد'), onPress: () => update(s => {
        const current = s.shifts.find(x => !x.end);
        if (active) return current ? { ...s, shifts: s.shifts.map(x => x.id === current.id ? { ...x, end: new Date().toISOString() } : x) } : s;
        return current ? s : { ...s, shifts: [{ id: makeId('A'), start: new Date().toISOString() }, ...s.shifts] };
      }) },
    ]);
  }
  return <Screen back title={tx('Attendance', 'الحضور')} subtitle={tx('Your workday starts here', 'يوم عملك يبدأ من هنا')}>
    <Card tinted><Pill text={active ? tx('On shift', 'داخل الوردية') : tx('Off shift', 'خارج الوردية')} /><Label size={28} bold>{active ? tx('Have a productive day', 'نتمنى لك يومًا مثمرًا') : tx('Ready when you are', 'جاهز لبدء يومك')}</Label>{active && <Label>{tx('Checked in', 'وقت الحضور')}: {date(active.start)}</Label>}<Button title={active ? tx('Check out', 'تسجيل الانصراف') : tx('Check in', 'تسجيل الحضور')} onPress={toggle} /></Card>
    <Card><Label bold size={18}>{tx('Assigned branch', 'الفرع المكلّف به')}</Label><Label>{tx('Citystars · Nasr City', 'سيتي ستارز · مدينة نصر')}</Label><Label muted>{tx('Demo schedule · 10:00–18:00', 'جدول تجريبي · 10:00–18:00')}</Label><Label size={12}>{tx('Location verification will be connected with attendance services.', 'التحقق من الموقع سيتم ربطه بخدمات الحضور.')}</Label></Card>
    <Card><RowLink title={tx('Attendance history', 'سجل الحضور')} detail={`${state.shifts.length} ${tx('recorded shifts', 'ورديات مسجلة')}`} icon="clock" onPress={() => router.push('/detail/attendance-log')} /></Card>
  </Screen>;
}
export function AttendanceLogScreen() {
  const { tx, date } = useUI(); const { state } = useDemo();
  return <Screen back title={tx('Attendance log', 'سجل الحضور')} subtitle={tx('A clear record of your workday', 'سجل واضح ليوم عملك')}>
    {!state.shifts.length && <Empty title={tx('No shifts recorded', 'لم تُسجّل ورديات')} detail={tx('Check in to start your first demo shift.', 'سجّل حضورك لبدء أول وردية تجريبية.')} />}
    {state.shifts.map(s => <Card key={s.id}><Pill text={s.end ? tx('Completed locally', 'مكتمل محليًا') : tx('Active', 'نشط')} /><Label bold>{tx('Citystars branch', 'فرع سيتي ستارز')}</Label><Label>{tx('In', 'الحضور')}: {date(s.start)}</Label><Label>{tx('Out', 'الانصراف')}: {s.end ? date(s.end) : '—'}</Label>{s.end && <Label muted>{Math.max(0, Math.round((new Date(s.end).getTime() - new Date(s.start).getTime()) / 60000))} {tx('minutes', 'دقيقة')}</Label>}</Card>)}
    <Button title={tx('Open attendance', 'فتح الحضور')} onPress={() => router.replace('/detail/attendance')} />
  </Screen>;
}
