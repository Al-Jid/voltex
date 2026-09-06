import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useRef, useState, type PropsWithChildren } from 'react';
import { makeId, products } from '../demo/DemoProvider';

export type Role = 'promoter' | 'supervisor' | 'admin';
export type Staff = { id: string; name: string; role: Role; branchId: string; supervisorId: string; active: boolean; email: string };
export type Branch = { id: string; name: string; address: string; active: boolean };
export type CatalogItem = { id: string; name: string; sku: string; price: number; active: boolean };
export type Review = { id: string; kind: 'request' | 'photo'; decision: 'approved' | 'changes'; note: string; date: string };
export type Task = { id: string; assigneeId: string; title: string; due: string; done: boolean };
type State = { version: 1; staff: Staff[]; branches: Branch[]; catalog: CatalogItem[]; reviews: Review[]; tasks: Task[]; targets: Record<string, number>; audit: { id: string; actor: Role; action: string; date: string }[] };
const seed = (): State => ({ version: 1,
  staff: [
    { id: 'u1', name: 'Hassan Gamal', role: 'promoter', branchId: 'b1', supervisorId: 's1', active: true, email: 'hassan@example.test' },
    { id: 'u2', name: 'Nour Samir', role: 'promoter', branchId: 'b1', supervisorId: 's1', active: true, email: 'nour@example.test' },
    { id: 'u3', name: 'Omar Khaled', role: 'promoter', branchId: 'b2', supervisorId: 's1', active: true, email: 'omar@example.test' },
    { id: 'u4', name: 'Mariam Ali', role: 'promoter', branchId: 'b3', supervisorId: 's2', active: true, email: 'mariam@example.test' },
    { id: 's1', name: 'Ahmed Ali', role: 'supervisor', branchId: 'b1', supervisorId: '', active: true, email: 'ahmed@example.test' },
    { id: 's2', name: 'Sara Mostafa', role: 'supervisor', branchId: 'b3', supervisorId: '', active: true, email: 'sara@example.test' },
    { id: 'a1', name: 'VOLTEX Admin', role: 'admin', branchId: 'b1', supervisorId: '', active: true, email: 'admin@example.test' },
  ],
  branches: [{ id: 'b1', name: 'Citystars', address: 'Nasr City, Cairo', active: true }, { id: 'b2', name: 'Cairo Festival City', address: 'New Cairo', active: true }, { id: 'b3', name: 'Mall of Arabia', address: '6th of October, Giza', active: true }],
  catalog: products.map(p => ({ id: p.id, name: p.name, sku: p.sku, price: p.price, active: true })),
  reviews: [], tasks: [], targets: { b1: 75000, b2: 60000, b3: 50000 }, audit: [],
});
type Value = { state: State; role: Role; setRole: (role: Role) => void; ready: boolean; storageError: boolean; change: (action: string, fn: (state: State) => State) => void };
const Context = createContext<Value | null>(null);
const KEY = '@voltex/management/v1';
export function ManagementProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<State>(seed); const [role, setRole] = useState<Role>('promoter'); const [ready, setReady] = useState(false); const [storageError, setStorageError] = useState(false);
  const queue = useRef<Promise<unknown>>(Promise.resolve()); const canPersist = useRef(true);
  useEffect(() => { let active = true;
    void AsyncStorage.getItem(KEY).then(raw => { if (!active || !raw) return; const value: unknown = JSON.parse(raw); if (valid(value)) setState(value); else { canPersist.current = false; setStorageError(true); } }).catch(() => { if (active) { canPersist.current = false; setStorageError(true); } }).finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => { if (!ready || !canPersist.current) return; queue.current = queue.current.then(() => AsyncStorage.setItem(KEY, JSON.stringify(state))).then(() => setStorageError(false)).catch(() => setStorageError(true)); }, [state, ready]);
  function change(action: string, fn: (s: State) => State) {
    const event = { id: makeId('E'), actor: role, action, date: new Date().toISOString() };
    setState(s => { const next = fn(s); return next === s ? s : { ...next, audit: [event, ...s.audit].slice(0, 500) }; });
  }
  return <Context.Provider value={{ state, role, setRole, ready, storageError, change }}>{children}</Context.Provider>;
}
export function useManagement() { const value = useContext(Context); if (!value) throw new Error('ManagementProvider required'); return value; }
function record(v: unknown): v is Record<string, unknown> { return typeof v === 'object' && v !== null && !Array.isArray(v); }
function valid(v: unknown): v is State {
  if (!record(v) || v.version !== 1 || !record(v.targets) || !Object.values(v.targets).every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0)) return false;
  const list = (x: unknown, check: (item: Record<string, unknown>) => boolean) => Array.isArray(x) && x.every(i => record(i) && typeof i.id === 'string' && check(i));
  const text = (x: unknown) => typeof x === 'string'; const date = (x: unknown) => text(x) && Number.isFinite(Date.parse(x as string));
  return list(v.staff, s => text(s.name) && ['promoter', 'supervisor', 'admin'].includes(String(s.role)) && text(s.branchId) && text(s.supervisorId) && text(s.email) && typeof s.active === 'boolean') &&
    list(v.branches, b => text(b.name) && text(b.address) && typeof b.active === 'boolean') &&
    list(v.catalog, p => text(p.name) && text(p.sku) && typeof p.price === 'number' && Number.isFinite(p.price) && p.price >= 0 && typeof p.active === 'boolean') &&
    list(v.reviews, r => ['request', 'photo'].includes(String(r.kind)) && ['approved', 'changes'].includes(String(r.decision)) && text(r.note) && date(r.date)) &&
    list(v.tasks, t => text(t.assigneeId) && text(t.title) && text(t.due) && typeof t.done === 'boolean') &&
    list(v.audit, e => ['promoter', 'supervisor', 'admin'].includes(String(e.actor)) && text(e.action) && date(e.date));
}
