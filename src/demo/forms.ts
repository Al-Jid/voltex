import { useDemo } from './DemoProvider';
/** Accept ASCII, Arabic and Persian digits, but never fractional/scientific quantities. */
export function wholeNumber(value: string) {
  const normalized = value.trim().replace(/[٠-٩]/g, d => String(d.charCodeAt(0) - 1632)).replace(/[۰-۹]/g, d => String(d.charCodeAt(0) - 1776));
  return /^\d+$/.test(normalized) ? Number(normalized) : NaN;
}
export function useDraft<T extends Record<string, string>>(key: string, defaults: T) {
  const { state, update } = useDemo();
  const value = { ...defaults, ...state.drafts[key] } as T;
  function set<K extends keyof T>(field: K, content: string) { update(s => ({ ...s, drafts: { ...s.drafts, [key]: { ...defaults, ...s.drafts[key], [field]: content } } })); }
  function clear() { update(s => { const drafts = { ...s.drafts }; delete drafts[key]; return { ...s, drafts }; }); }
  return { value, set, clear };
}
