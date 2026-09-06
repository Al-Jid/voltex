import { useRef, useState } from 'react';
import { Share, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Button, Card, Chips, Empty, Field, Label, Pill, RowLink, Screen, useUI } from '../../components/ui';
import { makeId, products, useDemo } from '../../demo/DemoProvider';
import { useDraft, wholeNumber } from '../../demo/forms';

export function SalesScreen() {
  const { state } = useDemo(); const { tx, money, date } = useUI();
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('today'); const [search, setSearch] = useState('');
  const start = new Date(); start.setHours(0, 0, 0, 0);
  if (period === 'week') start.setDate(start.getDate() - (start.getDay() + 6) % 7);
  if (period === 'month') start.setDate(1);
  const sales = state.sales.filter(s => { const p = products.find(p => p.id === s.productId); return new Date(s.date) >= start && `${s.id} ${p?.name} ${p?.ar} ${p?.sku}`.toLowerCase().includes(search.toLowerCase()); });
  const total = sales.reduce((n, s) => n + (products.find(p => p.id === s.productId)?.price ?? 0) * s.quantity, 0);
  return <Screen title={tx('Sales', 'المبيعات')} subtitle={tx('Small actions. Measurable impact.', 'خطوات بسيطة. نتائج ملموسة.')} action={{ icon: 'plus', label: tx('Log sale', 'تسجيل بيع'), run: () => router.push('/sheet/log-sale') }}>
    <Chips value={period} onChange={setPeriod} options={[{ value: 'today', label: tx('Today', 'اليوم') }, { value: 'week', label: tx('This week', 'هذا الأسبوع') }, { value: 'month', label: tx('This month', 'هذا الشهر') }]} />
    <Card tinted><Label muted>{tx('Recorded sales', 'المبيعات المسجلة')}</Label><Label bold size={32}>{money(total)}</Label><Label>{sales.length} {tx('transactions', 'عملية')} · {sales.reduce((n, s) => n + s.quantity, 0)} {tx('units', 'وحدة')}</Label></Card>
    <Field label={tx('Find a sale', 'ابحث عن عملية')} placeholder={tx('Product or reference number', 'المنتج أو رقم العملية')} value={search} onChangeText={setSearch} />
    {sales.length ? <Card>{sales.map(s => { const p = products.find(p => p.id === s.productId); return <RowLink key={s.id} icon="sales" title={tx(p?.name ?? '', p?.ar ?? '')} detail={`${s.id} · ${date(s.date)} · ${money((p?.price ?? 0) * s.quantity)}`} badge={s.local ? tx('Local', 'محلي') : tx('Sample', 'مثال')} onPress={() => router.push({ pathname: '/detail/sale', params: { id: s.id } })} />; })}</Card> : <Empty title={tx('No sales here yet', 'لا توجد مبيعات بعد')} detail={tx('Try a different period or record your first sale.', 'اختر فترة مختلفة أو سجّل أول عملية.')} />}
    <Button title={tx('Log a sale', 'تسجيل بيع')} onPress={() => router.push('/sheet/log-sale')} />
  </Screen>;
}
export function LogSaleScreen() {
  const { update } = useDemo(); const { tx, money } = useUI(); const draft = useDraft('sale', { productId: products[0]!.id, quantity: '1', note: '' });
  const { productId, quantity, note } = draft.value; const setProduct = (v: string) => draft.set('productId', v); const setQuantity = (v: string) => draft.set('quantity', v); const setNote = (v: string) => draft.set('note', v);
  const [error, setError] = useState(''); const saved = useRef(false);
  const p = products.find(p => p.id === productId) ?? products[0]!; const n = wholeNumber(quantity);
  function save() {
    if (!Number.isSafeInteger(n) || n < 1 || n > 999) { setError(tx('Enter a whole quantity from 1 to 999.', 'أدخل عددًا صحيحًا من 1 إلى 999.')); return; }
    if (saved.current) return; saved.current = true;
    const id = makeId('S'); update(s => ({ ...s, sales: [{ id, productId, quantity: n, note: note.trim(), date: new Date().toISOString(), local: true }, ...s.sales] }));
    draft.clear(); router.replace({ pathname: '/detail/sale', params: { id } });
  }
  return <Screen back title={tx('Log sale', 'تسجيل بيع')} subtitle={tx('Citystars · Sales report', 'سيتي ستارز · تقرير مبيعات')}>
    <Label muted size={12}>{tx('Your draft is saved as you type.', 'تُحفظ مسودتك أثناء الكتابة.')}</Label><Label bold>{tx('Choose a product', 'اختر المنتج')}</Label><Chips value={productId} onChange={setProduct} options={products.map(p => ({ value: p.id, label: tx(p.name, p.ar) }))} />
    <Card><Label bold size={20}>{tx(p.name, p.ar)}</Label><Label muted>{p.sku}</Label><Label>{money(p.price)} {tx('per unit', 'للوحدة')}</Label></Card>
    <Field label={tx('Quantity', 'الكمية')} value={quantity} onChangeText={v => { setQuantity(v); setError(''); }} keyboardType="number-pad" error={error} />
    <Field label={tx('Note (optional)', 'ملاحظة (اختياري)')} value={note} onChangeText={setNote} multiline maxLength={500} placeholder={tx('Add useful context…', 'أضف تفاصيل مفيدة…')} />
    <Card tinted><Label muted>{tx('Total value', 'القيمة الإجمالية')}</Label><Label bold size={28}>{money(Number.isFinite(n) && n > 0 ? p.price * n : 0)}</Label><Label size={12}>{tx('Reporting only. This does not change branch inventory.', 'تقرير مبيعات فقط. لا يغيّر مخزون الفرع.')}</Label></Card>
    <Button title={tx('Save sale on this device', 'حفظ العملية على الجهاز')} onPress={save} />
  </Screen>;
}
export function SaleDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>(); const { state } = useDemo(); const { tx, money, date } = useUI(); const sale = state.sales.find(s => s.id === id); const [shareError, setShareError] = useState('');
  if (!sale) return <Screen back title={tx('Sale detail', 'تفاصيل البيع')}><Empty title={tx('Sale not found', 'العملية غير موجودة')} detail={tx('Return to your sales list.', 'ارجع لقائمة المبيعات.')} /><Button title={tx('Sales', 'المبيعات')} onPress={() => router.replace('/(tabs)/sales')} /></Screen>;
  const p = products.find(p => p.id === sale.productId)!;
  return <Screen back title={tx('Sale detail', 'تفاصيل البيع')} subtitle={sale.id}>
    <Card tinted><Pill text={sale.local ? tx('Saved locally', 'محفوظ محليًا') : tx('Sample record', 'سجل تجريبي')} /><Label size={32} bold>{money(p.price * sale.quantity)}</Label><Label>{date(sale.date)}</Label></Card>
    <Card><Label bold size={20}>{tx(p.name, p.ar)}</Label><Label muted>{p.sku}</Label><Label>{tx('Quantity', 'الكمية')}: {sale.quantity}</Label><Label>{tx('Unit price', 'سعر الوحدة')}: {money(p.price)}</Label><Label>{tx('Branch: Citystars', 'الفرع: سيتي ستارز')}</Label><Label>{tx('Promoter', 'المروّج')}: {state.profile.name}</Label>{!!sale.note && <Label muted>{sale.note}</Label>}</Card>
    <Button title={tx('Share summary', 'مشاركة الملخص')} secondary onPress={() => { void Share.share({ message: `VOLTEX · ${sale.id}\n${tx(p.name, p.ar)} × ${sale.quantity}\n${money(p.price * sale.quantity)}\n${tx('Demo record — not an invoice', 'سجل تجريبي — ليس فاتورة')}` }).catch(() => setShareError(tx('Could not open sharing. Try again.', 'تعذّر فتح المشاركة. حاول مجددًا.'))); }} />
    {!!shareError && <Label>{shareError}</Label>}<Button title={tx('Back to sales', 'العودة للمبيعات')} onPress={() => router.replace('/(tabs)/sales')} />
  </Screen>;
}
