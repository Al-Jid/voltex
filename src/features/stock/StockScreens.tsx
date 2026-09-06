
import { useRef, useState } from 'react';
import { router, useLocalSearchParams } from 'expo-router';

import {
  Button,
  Card,
  Chips,
  Empty,
  Field,
  Label,
  Pill,
  Progress,
  Screen,
  useUI,
} from '../../components/ui';

import { makeId, products, useDemo } from '../../demo/DemoProvider';
import { useDraft, wholeNumber } from '../../demo/forms';
import { CountHistory } from './CountHistory';

export function StockScreen() {
  const { state } = useDemo();
  const { tx, date } = useUI();

  const [filter, setFilter] = useState<'all' | 'low' | 'out'>('all');
  const [search, setSearch] = useState('');

  const list = products.filter(
    (p) =>
      (filter === 'all' ||
        (filter === 'low'
          ? p.stock > 0 && p.stock < p.target
          : p.stock === 0)) &&
      `${p.name} ${p.ar} ${p.sku}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );

  return (
    <Screen
      title={tx('Branch stock', 'مخزون الفرع')}
      subtitle={tx(
        'Citystars · reference inventory',
        'سيتي ستارز · المخزون المرجعي',
      )}
    >
      <Card tinted>
        <Label bold size={28}>
          {products.reduce((n, p) => n + p.stock, 0)}{' '}
          {tx('units available', 'وحدة متاحة')}
        </Label>

        <Label muted>
          {tx(
            '2 products below minimum · sample inventory',
            'منتجان تحت الحد الأدنى · مخزون تجريبي',
          )}
        </Label>
      </Card>

      <Field
        label={tx('Search inventory', 'ابحث في المخزون')}
        placeholder={tx('Product name or SKU', 'اسم المنتج أو الكود')}
        value={search}
        onChangeText={setSearch}
      />

      <Chips
        value={filter}
        onChange={setFilter}
        options={[
          { value: 'all', label: tx('All', 'الكل') },
          { value: 'low', label: tx('Low stock', 'مخزون منخفض') },
          { value: 'out', label: tx('Out of stock', 'نفد المخزون') },
        ]}
      />

      {!list.length && (
        <Empty
          title={tx('No matching products', 'لا توجد منتجات مطابقة')}
          detail={tx(
            'Try another name or filter.',
            'جرّب اسمًا أو فلترًا آخر.',
          )}
        />
      )}

      {list.map((p) => {
        const count = state.counts.find((x) => x.productId === p.id);

        return (
          <Card key={p.id}>
            <Pill
              text={
                p.stock === 0
                  ? tx('Out of stock', 'نفد المخزون')
                  : p.stock < p.target
                    ? tx('Low stock', 'مخزون منخفض')
                    : tx('In stock', 'متوفر')
              }
            />

            <Label bold size={19}>
              {tx(p.name, p.ar)}
            </Label>

            <Label muted size={12}>
              {p.sku}
            </Label>

            <Label size={24} bold>
              {p.stock} {tx('units', 'وحدة')}
            </Label>

            <Progress value={p.stock / (p.target * 3)} />
            <CountHistory productId={p.id} />

            {count && (
              <Label size={12}>
                {tx('Your latest count', 'آخر جرد لك')}: {count.quantity} ·{' '}
                {date(count.date)} · {tx('local', 'محلي')}
              </Label>
            )}

            <Button
              title={tx('Submit count', 'تسجيل جرد')}
              secondary
              onPress={() =>
                router.push({
                  pathname: '/sheet/submit-count',
                  params: { productId: p.id },
                })
              }
            />

            {p.stock < p.target && (
              <Button
                title={tx('Request restock', 'طلب توريد')}
                onPress={() =>
                  router.push({
                    pathname: '/sheet/new-request',
                    params: { productId: p.id },
                  })
                }
              />
            )}
          </Card>
        );
      })}
    </Screen>
  );
}

export function SubmitCountScreen() {
  const params = useLocalSearchParams<{ productId: string }>();
  const { tx } = useUI();
  const { update } = useDemo();

  const draft = useDraft(`count:${params.productId ?? 'default'}`, {
    productId: products.some((p) => p.id === params.productId)
      ? params.productId
      : products[0]!.id,
    quantity: '',
    note: '',
  });

  const { productId, quantity, note } = draft.value;

  const setProduct = (v: string) => {
    draft.set('productId', v);
  };

  const setQuantity = (v: string) => {
    draft.set('quantity', v);
  };

  const setNote = (v: string) => {
    draft.set('note', v);
  };

  const [error, setError] = useState('');
  const saved = useRef(false);

  const p = products.find((product) => product.id === productId) ?? products[0]!;

  function save() {
    const n = wholeNumber(quantity);

    if (
      !quantity.trim() ||
      !Number.isSafeInteger(n) ||
      n < 0 ||
      n > 99999
    ) {
      setError(
        tx(
          'Enter a whole count from 0 to 99,999.',
          'أدخل عددًا صحيحًا من 0 إلى 99,999.',
        ),
      );
      return;
    }

    if (n !== p.stock && !note.trim()) {
      setError(
        tx(
          'Explain the difference from reference stock.',
          'وضّح سبب الفرق عن المخزون المرجعي.',
        ),
      );
      return;
    }

    if (saved.current) {
      return;
    }

    saved.current = true;

    update((s) => ({
      ...s,
      counts: [
        {
          id: makeId('C'),
          productId,
          quantity: n,
          note: note.trim(),
          date: new Date().toISOString(),
        },
        ...s.counts,
      ],
    }));

    draft.clear();
    router.replace('/(tabs)/stock');
  }

  return (
    <Screen
      back
      title={tx('Submit count', 'تسجيل جرد')}
      subtitle={tx(
        'Count what is physically at the branch',
        'سجّل العدد الفعلي الموجود بالفرع',
      )}
    >
      <Chips
        value={productId}
        onChange={setProduct}
        options={products.map((product) => ({
          value: product.id,
          label: tx(product.name, product.ar),
        }))}
      />

      <Card tinted>
        <Label bold>{tx(p.name, p.ar)}</Label>
        <Label>
          {tx('Reference stock', 'المخزون المرجعي')}: {p.stock}
        </Label>
      </Card>

      <Field
        label={tx('Actual quantity', 'الكمية الفعلية')}
        value={quantity}
        onChangeText={(value) => {
          setQuantity(value);
          setError('');
        }}
        keyboardType="number-pad"
      />

      <Field
        label={tx(
          'Count notes / reason for difference',
          'ملاحظات الجرد / سبب الفرق',
        )}
        value={note}
        onChangeText={setNote}
        multiline
        maxLength={500}
        error={error}
      />

      <Label muted>
        {tx(
          'Counts are observations. They do not overwrite reference inventory.',
          'الجرد تسجيل للملاحظة ولا يستبدل المخزون المرجعي.',
        )}
      </Label>

      <Button
        title={tx('Save count locally', 'حفظ الجرد محليًا')}
        onPress={save}
      />
    </Screen>
  );
}
