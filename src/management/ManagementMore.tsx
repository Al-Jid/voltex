import { router } from 'expo-router';
import { Button, Card, Label, RowLink, Screen, useUI } from '../components/ui';
import { useManagement } from './ManagementProvider';
import { ManagementNotice } from './navigation';
export function ManagementMore() {
  const m = useManagement(); const { tx } = useUI(); const admin = m.role === 'admin';
  return <Screen title={tx('More', 'المزيد')} subtitle={admin ? tx('Admin workspace', 'مساحة المدير') : tx('Supervisor workspace', 'مساحة المشرف')}><ManagementNotice /><Card tinted><Label bold size={24}>{admin ? 'VOLTEX Admin' : 'Ahmed Ali'}</Label><Label>{tx('Local demo identity', 'هوية تجريبية محلية')}</Label></Card><Card>
    {admin ? <><RowLink icon="reward" title={tx('Branch targets', 'مستهدفات الفروع')} onPress={() => router.push('/admin/targets')} /><RowLink icon="sales" title={tx('Organization reports', 'تقارير المؤسسة')} onPress={() => router.push('/admin/reports')} /><RowLink icon="request" title={tx('Audit history', 'سجل التغييرات')} onPress={() => router.push('/admin/audit')} /><RowLink icon="user" title={tx('Roles & access', 'الأدوار والصلاحيات')} onPress={() => router.push('/admin/access')} /></> : <><RowLink icon="request" title={tx('Assign a task', 'إسناد مهمة')} onPress={() => router.push('/supervisor/task')} /><RowLink icon="check" title={tx('Review queue', 'قائمة المراجعة')} onPress={() => router.push('/supervisor/reviews')} /></>}
    <RowLink icon="settings" title={tx('Language & appearance', 'اللغة والمظهر')} onPress={() => router.push('/detail/settings')} /><RowLink icon="book" title={tx('Workspace guide', 'دليل مساحة العمل')} onPress={() => router.push(admin ? '/admin/help' : '/supervisor/help')} /></Card><Button title={tx('Switch demo workspace', 'تبديل المساحة التجريبية')} onPress={() => router.push('/demo-role')} /><Button title={tx('Leave demo', 'الخروج من التجربة')} secondary onPress={() => { m.setRole('promoter'); router.replace('/login'); }} /></Screen>;
}
