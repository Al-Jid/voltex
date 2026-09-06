import { useRef, useState } from 'react';
import { Alert } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Card, Chips, Empty, Field, Label, Pill, RowLink, Screen, useUI } from '../../components/ui';
import { makeId, products, useDemo, type Request } from '../../demo/DemoProvider';
import { useDraft, wholeNumber } from '../../demo/forms';
import { ReviewFeedback } from '../../management/PromoterManagement';
export function RequestsScreen() {
  const { state } = useDemo(); const { tx, date } = useUI(); const [filter, setFilter] = useState<'all' | Request['status']>('all');
  const list = state.requests.filter(r => filter === 'all' || r.status === filter);
  return <Screen back title={tx('Requests', 'الطلبات')} subtitle={tx('Keep your branch moving', 'خلّي فرعك جاهز دايمًا')} action={{ icon: 'plus', label: tx('New request', 'طلب جديد'), run: () => router.push('/sheet/new-request') }}>
    <Chips value={filter} onChange={setFilter} options={[{ value: 'all', label: tx('All', 'الكل') }, { value: 'pending', label: tx('Pending', 'قيد المراجعة') }, { value: 'approved', label: tx('Approved', 'معتمد') }, { value: 'cancelled', label: tx('Cancelled', 'ملغي') }]} />
    {!list.length && <Empty title={tx('No requests in this view', 'لا توجد طلبات هنا')} detail={tx('Change the filter or create a request.', 'غيّر الفلتر أو أنشئ طلبًا.')} />}
    {list.map(r => <Card key={r.id}><Pill text={r.status === 'pending' ? tx('Awaiting review · local', 'بانتظار المراجعة · محلي') : r.status === 'approved' ? tx('Approved locally', 'معتمد محليًا') : tx('Cancelled', 'ملغي')} /><RowLink icon="request" title={r.type === 'restock' ? tx('Restock request', 'طلب توريد') : tx('Relocation request', 'طلب نقل')} detail={`${r.id} · ${date(r.date)}`} onPress={() => router.push({ pathname: '/detail/request', params: { id: r.id } })} /></Card>)}
    <Button title={tx('New request', 'طلب جديد')} onPress={() => router.push('/sheet/new-request')} />
  </Screen>;
}
export function NewRequestScreen() {
  const { productId: initialProduct } = useLocalSearchParams<{ productId: string }>(); const { update } = useDemo(); const { tx } = useUI();
  const draft = useDraft(`request:${initialProduct ?? 'default'}`, { type: 'restock', productId: products.some(p => p.id === initialProduct) ? initialProduct : products[0]!.id, quantity: '1', note: '' });
  const { productId, quantity, note } = draft.value; const type: Request['type'] = draft.value.type === 'relocate' ? 'relocate' : 'restock'; const setType = (v: Request['type']) => draft.set('type', v); const setProduct = (v: string) => draft.set('productId', v); const setQuantity = (v: string) => draft.set('quantity', v); const setNote = (v: string) => draft.set('note', v); const [error, setError] = useState(''); const saved = useRef(false);
  function save() {
    const n = wholeNumber(quantity);
    if (!Number.isSafeInteger(n) || n < 1 || n > 9999) { setError(tx('Quantity must be a whole number from 1 to 9,999.', 'الكمية عدد صحيح من 1 إلى 9,999.')); return; }
    if (note.trim().length < 5) { setError(tx('Add a short reason (at least 5 characters).', 'أضف سببًا مختصرًا لا يقل عن 5 أحرف.')); return; }
    if (saved.current) return; saved.current = true; const id = makeId('R');
    update(s => ({ ...s, requests: [{ id, type, productId, quantity: n, note: note.trim(), date: new Date().toISOString(), status: 'pending' }, ...s.requests] })); draft.clear(); router.replace({ pathname: '/detail/request', params: { id } });
  }
  return <Screen back title={tx('New request', 'طلب جديد')} subtitle={tx('Give your supervisor the context they need', 'وضّح لمشرفك تفاصيل احتياجك')}>
    <Chips value={type} onChange={setType} options={[{ value: 'restock', label: tx('Restock', 'توريد مخزون') }, { value: 'relocate', label: tx('Relocate stock', 'نقل مخزون') }]} />
    <Label bold>{tx('Product', 'المنتج')}</Label><Chips value={productId} onChange={setProduct} options={products.map(p => ({ value: p.id, label: tx(p.name, p.ar) }))} />
    <Card tinted><Label>{tx('Receiving branch: Citystars', 'الفرع المستلم: سيتي ستارز')}</Label>{type === 'relocate' && <Label muted>{tx('Your supervisor assigns the source branch during review.', 'يحدّد المشرف الفرع المورّد أثناء المراجعة.')}</Label>}</Card>
    <Field label={tx('Quantity', 'الكمية')} value={quantity} onChangeText={setQuantity} keyboardType="number-pad" />
    <Field label={tx('Reason', 'السبب')} value={note} onChangeText={setNote} multiline maxLength={500} placeholder={tx('What does the branch need, and why?', 'ماذا يحتاج الفرع؟ ولماذا؟')} error={error} />
    <Button title={tx('Save request locally', 'حفظ الطلب محليًا')} onPress={save} />
  </Screen>;
}
export function RequestDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>(); const { state, update } = useDemo(); const { tx, date } = useUI(); const r = state.requests.find(x => x.id === id);
  if (!r) return <Screen back title={tx('Request detail', 'تفاصيل الطلب')}>
    <Empty title={id ? tx('This request is no longer available', 'هذا الطلب لم يعد متاحًا') : tx('Choose a request to view', 'اختر طلبًا لعرض تفاصيله')} detail={tx('Open a saved request below, or create one.', 'افتح طلبًا محفوظًا بالأسفل أو أنشئ طلبًا جديدًا.')} />
    {state.requests.length > 0 && <Card>{state.requests.map(item => <RowLink key={item.id} icon="request" title={item.type === 'restock' ? tx('Restock request', 'طلب توريد') : tx('Relocation request', 'طلب نقل')} detail={`${item.id} · ${date(item.date)}`} onPress={() => router.replace({ pathname: '/detail/request', params: { id: item.id } })} />)}</Card>}
    <Button title={tx('New request', 'طلب جديد')} onPress={() => router.push('/sheet/new-request')} />
    <Button title={tx('All requests', 'كل الطلبات')} secondary onPress={() => router.replace('/detail/requests')} />
  </Screen>;
  const p = products.find(p => p.id === r.productId)!;
  return <Screen back title={tx('Request detail', 'تفاصيل الطلب')} subtitle={r.id}>
    <ReviewFeedback id={r.id} kind="request" />
    <Card tinted><Pill text={r.status === 'pending' ? tx('Pending review', 'بانتظار المراجعة') : r.status === 'cancelled' ? tx('Cancelled', 'ملغي') : tx('Approved', 'معتمد')} /><Label size={24} bold>{r.type === 'restock' ? tx('Restock', 'توريد مخزون') : tx('Relocate stock', 'نقل مخزون')}</Label><Label>{tx(p.name, p.ar)} × {r.quantity}</Label></Card>
    <Card><Label bold>{tx('Request details', 'تفاصيل الطلب')}</Label><Label>{r.note}</Label><Label muted>{tx('To: Citystars', 'إلى: سيتي ستارز')}</Label><Label muted>{date(r.date)}</Label></Card>
    <Card><Label bold>{tx('Activity', 'النشاط')}</Label><Label>✓ {tx('Created on this device', 'تم الإنشاء على الجهاز')}</Label><Label>{r.status === 'cancelled' ? tx('Cancelled by you', 'أُلغي بواسطتك') : tx('Demo reviews are local. Server review and fulfillment are not connected.', 'مراجعات التجربة محلية. مراجعة الخادم وتنفيذ الطلب غير مربوطين.')}</Label></Card>
    {r.status === 'pending' && <Button title={tx('Cancel request', 'إلغاء الطلب')} secondary onPress={() => Alert.alert(tx('Cancel this request?', 'إلغاء هذا الطلب؟'), tx('It will remain in your history.', 'سيظل ظاهرًا في السجل.'), [{ text: tx('Keep request', 'الاحتفاظ بالطلب'), style: 'cancel' }, { text: tx('Cancel request', 'إلغاء الطلب'), style: 'destructive', onPress: () => update(s => ({ ...s, requests: s.requests.map(x => x.id === r.id ? { ...x, status: 'cancelled' } : x) })) }])} />}
    <Button title={tx('All requests', 'كل الطلبات')} onPress={() => router.replace('/detail/requests')} />
  </Screen>;
}
