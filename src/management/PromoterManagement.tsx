import { Button, Card, Label, Pill, useUI } from '../components/ui';
import { useManagement } from './ManagementProvider';
export function MyAssignedTasks() {
  const m = useManagement(); const { tx } = useUI(); const tasks = m.state.tasks.filter(t => t.assigneeId === 'u1');
  if (!tasks.length) return null;
  return <><Label bold size={18}>{tx('Tasks from your supervisor', 'مهام من مشرفك')}</Label>{tasks.map(t => <Card key={t.id}><Label bold>{t.title}</Label><Label muted>{t.due}</Label><Pill text={t.done ? tx('Completed locally', 'مكتملة محليًا') : tx('To do', 'مطلوبة')} /><Button disabled={t.done} secondary title={t.done ? tx('Completed', 'مكتملة') : tx('Mark complete', 'تحديد كمكتملة')} onPress={() => m.change(`Task ${t.id}: completed by promoter`, s => ({ ...s, tasks: s.tasks.map(x => x.id === t.id ? { ...x, done: true } : x) }))} /></Card>)}</>;
}
export function ReviewFeedback({ id, kind }: { id: string; kind: 'request' | 'photo' }) {
  const m = useManagement(); const { tx, date } = useUI(); const review = m.state.reviews.find(r => r.id === id && r.kind === kind);
  if (!review) return null;
  return <Card tinted><Label bold>{tx('Supervisor feedback', 'ملاحظات المشرف')}</Label><Pill text={review.decision === 'approved' ? tx('Approved locally', 'معتمد محليًا') : tx('Changes requested', 'مطلوب تعديل')} />{!!review.note && <Label>{review.note}</Label>}<Label muted size={12}>{date(review.date)}</Label>{review.decision === 'changes' && <Label size={12}>{kind === 'request' ? tx('Create a corrected request with the required details.', 'أنشئ طلبًا مصححًا بالتفاصيل المطلوبة.') : tx('Update notes or capture a clearer photo, then ask for review.', 'حدّث الملاحظات أو أضف صورة أوضح ثم اطلب المراجعة.')}</Label>}</Card>;
}
