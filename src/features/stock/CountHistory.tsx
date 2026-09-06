import { useState } from 'react';
import { View } from 'react-native';
import { Button, Card, Label, useUI } from '../../components/ui';
import { useDemo } from '../../demo/DemoProvider';

export function CountHistory({ productId }: { productId: string }) {
  const { state } = useDemo(); const { tx, date } = useUI(); const [open, setOpen] = useState(false);
  const counts = state.counts.filter(c => c.productId === productId);
  if (!counts.length) return null;
  return <View style={{ gap: 12 }}>
    <Button title={open ? tx('Hide count history', 'إخفاء سجل الجرد') : tx(`View count history (${counts.length})`, `عرض سجل الجرد (${counts.length})`)} secondary onPress={() => setOpen(v => !v)} />
    {open && counts.map(c => <Card key={c.id}><Label bold>{c.quantity} {tx('units observed', 'وحدة مسجّلة')}</Label><Label muted size={12}>{date(c.date)} · {tx('Local observation', 'ملاحظة محلية')}</Label><Label>{c.note || tx('No discrepancy notes.', 'لا توجد ملاحظات فروق.')}</Label></Card>)}
  </View>;
}
