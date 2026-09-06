import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useRef, useState, type PropsWithChildren } from 'react';

export type Product = { id: string; name: string; ar: string; sku: string; price: number; stock: number; target: number };
export const products: Product[] = [
  { id: 'p1', name: 'VOLTEX Air 12', ar: 'فولتكس إير 12', sku: 'VX-AC12', price: 18500, stock: 18, target: 8 },
  { id: 'p2', name: 'VOLTEX Cool 320', ar: 'فولتكس كول 320', sku: 'VX-RF320', price: 24900, stock: 4, target: 8 },
  { id: 'p3', name: 'VOLTEX Wash 8', ar: 'فولتكس واش 8', sku: 'VX-WM8', price: 15750, stock: 12, target: 6 },
  { id: 'p4', name: 'VOLTEX Vision 55', ar: 'فولتكس فيجن 55', sku: 'VX-TV55', price: 21200, stock: 0, target: 5 },
];
export type Sale = { id: string; productId: string; quantity: number; date: string; note: string; local: boolean };
export type Request = { id: string; type: 'restock' | 'relocate'; productId: string; quantity: number; note: string; date: string; status: 'pending' | 'approved' | 'cancelled' };
export type Shift = { id: string; start: string; end?: string };
export type ShelfPhoto = { id: string; uri: string; note: string; date: string; source: 'camera' | 'library'; coords?: { latitude: number; longitude: number }; };
export type Count = { id: string; productId: string; quantity: number; note: string; date: string };
type State = { version: 1; sales: Sale[]; requests: Request[]; shifts: Shift[]; photos: ShelfPhoto[]; counts: Count[]; readNotifications: string[]; joined: boolean; completedLessons: string[]; profile: { name: string; phone: string }; notifications: boolean; drafts: Record<string, Record<string, string>> };
const seed = (): State => ({ version: 1,
  sales: [{ id: 'S-1042', productId: 'p1', quantity: 1, date: new Date().toISOString(), note: 'Sample sale / عملية تجريبية', local: false }, { id: 'S-1041', productId: 'p3', quantity: 2, date: new Date(Date.now() - 86400000).toISOString(), note: '', local: false }],
  requests: [{ id: 'R-208', type: 'restock', productId: 'p2', quantity: 6, note: 'Sample restock request / طلب تجريبي', date: new Date().toISOString(), status: 'pending' }],
  shifts: [], photos: [], counts: [], readNotifications: [], joined: false, completedLessons: [], profile: { name: 'Hassan Gamal', phone: '' }, notifications: true, drafts: {},
});
type Value = { state: State; ready: boolean; storageError: boolean; update: (fn: (state: State) => State) => void; reset: () => void };
const Context = createContext<Value | null>(null);
const KEY = '@voltex/demo/v1';
let sequence = 0;
export const makeId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${++sequence}`;
export function DemoProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<State>(seed);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const queue = useRef<Promise<unknown>>(Promise.resolve());
  const canPersist = useRef(true);
  useEffect(() => {
    let active = true;
    void AsyncStorage.getItem(KEY).then(raw => {
      if (!raw || !active) return;
      const saved = JSON.parse(raw) as Partial<State>;
      if (validState(saved)) setState({ ...saved, drafts: validDrafts(saved.drafts) ? saved.drafts : {} });
      else { canPersist.current = false; setStorageError(true); }
    }).catch(() => { if (active) { canPersist.current = false; setStorageError(true); } }).finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!ready || !canPersist.current) return;
    queue.current = queue.current.then(() => AsyncStorage.setItem(KEY, JSON.stringify(state))).then(() => setStorageError(false)).catch(() => setStorageError(true));
  }, [state, ready]);
  return <Context.Provider value={{ state, ready, storageError, update: setState, reset: () => setState(seed()) }}>{children}</Context.Provider>;
}
export function useDemo() { const value = useContext(Context); if (!value) throw new Error('DemoProvider required'); return value; }

function record(v: unknown): v is Record<string, unknown> { return typeof v === 'object' && v !== null && !Array.isArray(v); }
function strings(v: unknown): v is string[] { return Array.isArray(v) && v.every(x => typeof x === 'string'); }
function validDrafts(v: unknown): v is State['drafts'] { return record(v) && Object.values(v).every(d => record(d) && Object.values(d).every(x => typeof x === 'string')); }
function validState(v: unknown): v is State {
  if (!record(v) || v.version !== 1 || !record(v.profile) || typeof v.profile.name !== 'string' || typeof v.profile.phone !== 'string' || typeof v.notifications !== 'boolean' || typeof v.joined !== 'boolean' || !strings(v.completedLessons) || !strings(v.readNotifications)) return false;
  const date = (x: unknown) => typeof x === 'string' && Number.isFinite(Date.parse(x));
  const quantity = (x: unknown) => typeof x === 'number' && Number.isSafeInteger(x) && x >= 0;
  const product = (x: unknown) => products.some(p => p.id === x);
  const list = (x: unknown, check: (item: Record<string, unknown>) => boolean) => Array.isArray(x) && x.every(i => record(i) && typeof i.id === 'string' && check(i));
  return list(v.sales, s => product(s.productId) && quantity(s.quantity) && date(s.date) && typeof s.note === 'string' && typeof s.local === 'boolean') &&
    list(v.requests, r => product(r.productId) && quantity(r.quantity) && date(r.date) && typeof r.note === 'string' && (r.type === 'restock' || r.type === 'relocate') && ['pending', 'approved', 'cancelled'].includes(String(r.status))) &&
    list(v.shifts, s => date(s.start) && (s.end === undefined || date(s.end))) &&
    list(v.counts, c => product(c.productId) && quantity(c.quantity) && date(c.date) && typeof c.note === 'string') &&
    list(v.photos, p => typeof p.uri === 'string' && typeof p.note === 'string' && date(p.date) && (p.source === 'camera' || p.source === 'library') && (p.coords === undefined || (record(p.coords) && typeof p.coords.latitude === 'number' && typeof p.coords.longitude === 'number')));
}
