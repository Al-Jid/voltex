import { useRef, useState } from 'react';
import { Alert, Image } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Card, Chips, Empty, Field, Label, Pill, RowLink, Screen, useUI } from '../components/ui';
import { makeId, products, useDemo } from '../demo/DemoProvider';
import { ManagementNotice } from './navigation';
import { useManagement } from './ManagementProvider';

function useTeam() { const m = useManagement(); return m.state.staff.filter(s => s.role === 'promoter' && s.supervisorId === 's1'); }
export function SupervisorHome() {
  const { tx, money } = useUI(); const team = useTeam(); const m = useManagement(); const { state } = useDemo(); const linked = team.some(u => u.id === 'u1');
  const pending = linked ? state.requests.filter(r => r.status === 'pending' && !m.state.reviews.some(x => x.id === r.id)).length + state.photos.filter(p => !m.state.reviews.some(x => x.id === p.id)).length : 0;
  const sales = linked ? state.sales.reduce((n, s) => n + s.quantity * (products.find(p => p.id === s.productId)?.price ?? 0), 0) : 0;
  return <Screen title={tx('Supervisor overview', 'نظرة المشرف')} subtitle={tx('Ahmed Ali · Assigned team', 'أحمد علي · الفريق المسند')}><ManagementNotice />
    <Card tinted><Pill text={tx('YOUR FIELD TEAM', 'فريقك الميداني')} /><Label size={32} bold>{team.filter(u => u.active).length} {tx('active promoters', 'مروّجين نشطين')}</Label><Label>{pending} {tx('items awaiting review', 'عناصر تنتظر المراجعة')}</Label><Button title={tx('Open review queue', 'فتح قائمة المراجعة')} onPress={() => router.push('/supervisor/reviews')} /></Card>
    <Card><Label bold>{tx('Linked demo sales', 'المبيعات التجريبية المرتبطة')}</Label><Label size={28} bold>{money(sales)}</Label><Label muted>{tx('Hassan’s local records are linked. Other team members are directory samples without transactions.', 'سجلات حسن المحلية مرتبطة. باقي الأعضاء نماذج دليل بدون معاملات.')}</Label></Card>
    <Card><RowLink icon="user" title={tx('My team', 'فريقي')} onPress={() => router.push('/supervisor/team')} /><RowLink icon="request" title={tx('Assign a task', 'إسناد مهمة')} detail={tx('Set an owner and due date', 'حدّد مسؤولًا وموعدًا')} onPress={() => router.push('/supervisor/task')} /><RowLink icon="sales" title={tx('Team reports', 'تقارير الفريق')} onPress={() => router.push('/supervisor/reports')} /></Card>
  </Screen>;
}
export function TeamScreen() {
  const { tx } = useUI(); const team = useTeam(); const m = useManagement(); const { state } = useDemo(); const [search, setSearch] = useState(''); const [filter, setFilter] = useState<'all' | 'active'>('all');
  const list = team.filter(u => (filter === 'all' || u.active) && u.name.toLowerCase().includes(search.toLowerCase()));
  return <Screen title={tx('My team', 'فريقي')} subtitle={tx('Only promoters assigned to Ahmed Ali', 'المروّجون المسندون لأحمد علي فقط')}><ManagementNotice /><Field label={tx('Find a teammate', 'ابحث عن عضو')} value={search} onChangeText={setSearch} /><Chips value={filter} onChange={setFilter} options={[{ value: 'all', label: tx('All', 'الكل') }, { value: 'active', label: tx('Active', 'نشط') }]} />
    {!list.length && <Empty title={tx('No matching members', 'لا يوجد أعضاء مطابقون')} detail={tx('Change the search or filter.', 'غيّر البحث أو الفلتر.')} />}
    {list.map(u => <Card key={u.id}><RowLink icon="user" title={u.id === 'u1' ? state.profile.name : u.name} detail={m.state.branches.find(b => b.id === u.branchId)?.name} badge={u.active ? tx('Active', 'نشط') : tx('Inactive', 'معطّل')} onPress={() => router.push({ pathname: '/supervisor/member', params: { id: u.id } })} /></Card>)}
    <Button title={tx('Assign a task', 'إسناد مهمة')} onPress={() => router.push('/supervisor/task')} />
  </Screen>;
}
export function MemberScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>(); const team = useTeam(); const m = useManagement(); const { state } = useDemo(); const { tx, money, date } = useUI(); const u = team.find(u => u.id === id);
  if (!u) return <Screen back title={tx('Team member', 'عضو الفريق')}><Empty title={tx('Select a member of your team', 'اختر عضوًا من فريقك')} detail={tx('This member is unavailable in your assigned team.', 'هذا العضو غير متاح ضمن فريقك المسند.')} /><Button title={tx('Open team', 'فتح الفريق')} onPress={() => router.replace('/supervisor/team')} /></Screen>;
  const tasks = m.state.tasks.filter(t => t.assigneeId === u.id);
  return <Screen back title={u.id === 'u1' ? state.profile.name : u.name} subtitle={m.state.branches.find(b => b.id === u.branchId)?.name}><ManagementNotice /><Card tinted><Pill text={u.active ? tx('Active promoter', 'مروّج نشط') : tx('Inactive', 'معطّل')} /><Label>{u.email}</Label></Card>
    {u.id === 'u1' ? <><Card><Label bold>{tx('Linked sales', 'المبيعات المرتبطة')}</Label><Label size={28} bold>{money(state.sales.reduce((n, s) => n + s.quantity * (products.find(p => p.id === s.productId)?.price ?? 0), 0))}</Label><Label>{state.shifts.some(s => !s.end) ? tx('Currently checked in · local', 'مسجل حضور حاليًا · محلي') : tx('No active local shift', 'لا توجد وردية محلية نشطة')}</Label></Card><Card><Label bold>{tx('Recent attendance', 'آخر سجلات الحضور')}</Label>{state.shifts.length ? state.shifts.slice(0, 5).map(s => <Label key={s.id} size={12}>{date(s.start)} → {s.end ? date(s.end) : tx('Open', 'مفتوحة')}</Label>) : <Label muted>{tx('No shifts recorded yet.', 'لا توجد ورديات مسجلة بعد.')}</Label>}</Card></> : <Empty title={tx('Directory sample', 'نموذج عضو في الدليل')} detail={tx('No sales or attendance have been reported for this sample member.', 'لم تُسجّل مبيعات أو حضور لهذا العضو التجريبي.')} />}
    <Label bold size={18}>{tx('Assigned tasks', 'المهام المسندة')}</Label>{!tasks.length && <Label muted>{tx('No tasks assigned yet.', 'لا توجد مهام مسندة بعد.')}</Label>}{tasks.map(t => <Card key={t.id}><Label bold>{t.title}</Label><Label muted>{t.due}</Label><Pill text={t.done ? tx('Complete', 'مكتملة') : tx('Open', 'مفتوحة')} /><Button secondary title={t.done ? tx('Reopen task', 'إعادة فتح المهمة') : tx('Mark complete', 'تحديد كمكتملة')} onPress={() => m.change(`Task ${t.id}: ${t.done ? 'reopened' : 'completed'}`, s => ({ ...s, tasks: s.tasks.map(x => x.id === t.id ? { ...x, done: !x.done } : x) }))} /></Card>)}
    <Button disabled={!u.active} title={tx('Assign task', 'إسناد مهمة')} onPress={() => router.push({ pathname: '/supervisor/task', params: { id: u.id } })} />
  </Screen>;
}
export function TaskScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>(); const team = useTeam().filter(u => u.active); const m = useManagement(); const { tx } = useUI(); const [owner, setOwner] = useState(id ?? team[0]?.id ?? ''); const [title, setTitle] = useState(''); const [due, setDue] = useState(new Date().toISOString().slice(0, 10)); const [error, setError] = useState(''); const saved = useRef(false);
  function save() {
    const parsed = new Date(due + 'T12:00:00');
    if (!team.some(u => u.id === owner) || title.trim().length < 4 || !/^\d{4}-\d{2}-\d{2}$/.test(due) || !Number.isFinite(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== due) { setError(tx('Choose a team member, a clear title and a valid YYYY-MM-DD date.', 'اختر عضوًا وعنوانًا واضحًا وتاريخًا صحيحًا بصيغة YYYY-MM-DD.')); return; }
    if (saved.current) return; saved.current = true; const taskId = makeId('T');
    m.change(`Task assigned: ${title.trim()}`, s => ({ ...s, tasks: [{ id: taskId, assigneeId: owner, title: title.trim(), due, done: false }, ...s.tasks] })); router.replace({ pathname: '/supervisor/member', params: { id: owner } });
  }
  return <Screen back title={tx('Assign task', 'إسناد مهمة')}><ManagementNotice /><Label bold>{tx('Team member', 'عضو الفريق')}</Label><Chips value={owner} onChange={setOwner} options={team.map(u => ({ value: u.id, label: u.name }))} /><Field label={tx('Task', 'المهمة')} value={title} onChangeText={setTitle} maxLength={160} multiline /><Field label={tx('Due date · YYYY-MM-DD', 'الموعد · YYYY-MM-DD')} value={due} onChangeText={setDue} autoCapitalize="none" /><Label>{error}</Label><Button disabled={!team.length} title={tx('Save assignment locally', 'حفظ الإسناد محليًا')} onPress={save} /></Screen>;
}
export function ReviewsScreen() {
  const { state } = useDemo(); const m = useManagement(); const team = useTeam(); const { tx, date } = useUI(); const [filter, setFilter] = useState<'pending' | 'reviewed'>('pending'); const permitted = team.some(u => u.id === 'u1');
  const items = permitted ? [...state.requests.filter(r => r.status !== 'cancelled').map(r => ({ id: r.id, kind: 'request' as const, title: tx('Stock request', 'طلب مخزون'), date: r.date })), ...state.photos.map(p => ({ id: p.id, kind: 'photo' as const, title: tx('Shelf photo', 'صورة رف'), date: p.date }))].filter(i => m.state.reviews.some(r => r.id === i.id && r.kind === i.kind) === (filter === 'reviewed')) : [];
  return <Screen title={tx('Reviews', 'المراجعات')} subtitle={tx('Linked records from your assigned team', 'سجلات مرتبطة من فريقك المسند')}><ManagementNotice /><Chips value={filter} onChange={setFilter} options={[{ value: 'pending', label: tx('Awaiting review', 'بانتظار المراجعة') }, { value: 'reviewed', label: tx('Reviewed', 'تمت المراجعة') }]} />{!items.length && <Empty title={tx('Nothing in this queue', 'لا توجد عناصر في القائمة')} detail={tx('Create a request or shelf photo in the promoter demo to review it here.', 'أنشئ طلبًا أو صورة في دور المروّج لتراجعها هنا.')} />}{items.map(i => <Card key={i.id}><RowLink icon={i.kind === 'photo' ? 'camera' : 'request'} title={i.title} detail={`${i.id} · ${date(i.date)}`} onPress={() => router.push({ pathname: '/supervisor/review', params: { id: i.id, kind: i.kind } })} /></Card>)}</Screen>;
}
export function ReviewScreen() {
  const { id, kind } = useLocalSearchParams<{ id?: string; kind?: string }>(); const { state, update } = useDemo(); const m = useManagement(); const team = useTeam(); const { tx, date } = useUI(); const [note, setNote] = useState(''); const [error, setError] = useState(''); const [imageFailed, setImageFailed] = useState(false);
  const request = kind === 'request' ? state.requests.find(r => r.id === id) : undefined; const photo = kind === 'photo' ? state.photos.find(p => p.id === id) : undefined; const review = m.state.reviews.find(r => r.id === id && r.kind === kind);
  if ((!request && !photo) || !team.some(u => u.id === 'u1')) return <Screen back title={tx('Review', 'المراجعة')}><Empty title={tx('No accessible item selected', 'لم يُحدد عنصر متاح')} detail={tx('Open an item from your team’s review queue.', 'افتح عنصرًا من قائمة مراجعات فريقك.')} /><Button title={tx('Open reviews', 'فتح المراجعات')} onPress={() => router.replace('/supervisor/reviews')} /></Screen>;
  function decide(decision: 'approved' | 'changes') {
    if (decision === 'changes' && note.trim().length < 5) { setError(tx('Explain the required changes (at least 5 characters).', 'وضّح التعديلات المطلوبة في 5 أحرف على الأقل.')); return; }
    Alert.alert(tx('Save local review?', 'حفظ المراجعة المحلية؟'), tx('The decision will appear in the promoter demo. No server action is performed.', 'سيظهر القرار في دور المروّج التجريبي، بدون إجراء على خادم.'), [{ text: tx('Cancel', 'إلغاء'), style: 'cancel' }, { text: tx('Confirm', 'تأكيد'), onPress: () => {
      if (!id || (kind !== 'photo' && kind !== 'request')) return;
      m.change(`Review ${id}: ${decision}`, s => ({ ...s, reviews: [{ id, kind, decision, note: note.trim(), date: new Date().toISOString() }, ...s.reviews.filter(r => !(r.id === id && r.kind === kind))] }));
      if (request) update(s => ({ ...s, requests: s.requests.map(r => r.id === id && r.status !== 'cancelled' ? { ...r, status: decision === 'approved' ? 'approved' : 'pending' } : r) }));
      router.replace('/supervisor/reviews');
    } }]);
  }
  return <Screen back title={tx('Review detail', 'تفاصيل المراجعة')} subtitle={id}><ManagementNotice /><Card tinted><Label bold>{state.profile.name}</Label><Label>{tx('Citystars · local record', 'سيتي ستارز · سجل محلي')}</Label></Card>
    {request && <Card><Label bold>{products.find(p => p.id === request.productId)?.name} × {request.quantity}</Label><Label>{request.note}</Label><Label muted>{date(request.date)}</Label><Pill text={request.status === 'cancelled' ? tx('Cancelled', 'ملغي') : tx('Stock request', 'طلب مخزون')} /></Card>}
    {photo && <Card>{imageFailed ? <Label>{tx('Local image file unavailable.', 'ملف الصورة المحلي غير متاح.')}</Label> : <Image source={{ uri: photo.uri }} accessibilityLabel={tx('Shelf photo for review', 'صورة الرف للمراجعة')} onError={() => setImageFailed(true)} style={{ width: '100%', aspectRatio: 4 / 3, borderRadius: 12 }} />}<Label>{photo.note || tx('No notes', 'بدون ملاحظات')}</Label><Label muted>{date(photo.date)}</Label></Card>}
    {review && <Card><Label bold>{tx('Previous review', 'المراجعة السابقة')}</Label><Label>{review.decision === 'approved' ? tx('Approved locally', 'معتمد محليًا') : tx('Changes requested', 'مطلوب تعديل')}</Label><Label>{review.note}</Label></Card>}
    <Field label={tx('Review notes', 'ملاحظات المراجعة')} value={note} onChangeText={setNote} multiline maxLength={500} error={error} />
    <Button disabled={request?.status === 'cancelled' || imageFailed} title={tx('Approve locally', 'اعتماد محلي')} onPress={() => decide('approved')} /><Button disabled={request?.status === 'cancelled'} secondary title={tx('Request changes', 'طلب تعديلات')} onPress={() => decide('changes')} />
  </Screen>;
}
export function SupervisorReports() {
  const { tx, money } = useUI(); const { state } = useDemo(); const team = useTeam(); const [period, setPeriod] = useState<'today' | 'month'>('today'); const start = new Date(); start.setHours(0, 0, 0, 0); if (period === 'month') start.setDate(1);
  const sales = team.some(u => u.id === 'u1') ? state.sales.filter(s => new Date(s.date) >= start) : [];
  return <Screen title={tx('Team reports', 'تقارير الفريق')}><ManagementNotice /><Chips value={period} onChange={setPeriod} options={[{ value: 'today', label: tx('Today', 'اليوم') }, { value: 'month', label: tx('This month', 'هذا الشهر') }]} /><Card tinted><Label muted>{tx('Linked sales value', 'قيمة المبيعات المرتبطة')}</Label><Label size={32} bold>{money(sales.reduce((n, s) => n + s.quantity * (products.find(p => p.id === s.productId)?.price ?? 0), 0))}</Label><Label>{sales.reduce((n, s) => n + s.quantity, 0)} {tx('units', 'وحدة')}</Label></Card><Label muted>{tx('Only Hassan’s records are linked. No activity is assumed for other members.', 'سجلات حسن فقط مرتبطة. لا نفترض وجود نشاط للأعضاء الآخرين.')}</Label>{team.map(u => <Card key={u.id}><RowLink icon="user" title={u.id === 'u1' ? state.profile.name : u.name} detail={u.id === 'u1' ? `${sales.length} ${tx('sales records', 'سجلات بيع')}` : tx('No linked activity', 'لا يوجد نشاط مرتبط')} onPress={() => router.push({ pathname: '/supervisor/member', params: { id: u.id } })} /></Card>)}</Screen>;
}
