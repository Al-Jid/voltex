import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react';
import { useColorScheme } from 'react-native';

export type ThemeMode = 'light' | 'dark' | 'system';
export type Language = 'en' | 'ar';
const light = { background: '#FFFAFF', text: '#202024', muted: '#53505C', primary: '#4D3BC1', onPrimary: '#FFFFFF', border: '#A8A1AB', field: '#FDF8FF', notice: '#E5DEFF', circle: '#EEEFF0', surface: '#FFFFFF', error: '#AC2533' };
const dark: typeof light = { background: '#14121C', text: '#F5F1FC', muted: '#C0B8CF', primary: '#AD9BFF', onPrimary: '#211347', border: '#696174', field: '#1D1928', notice: '#30264D', circle: '#2D2936', surface: '#231F2E', error: '#FF9DA9' };
const KEY = '@voltex/preferences/v1';
type Preferences = { language: Language; mode: ThemeMode };
type Value = Preferences & { colors: typeof light; isDark: boolean; setLanguage: (value: Language) => void; setMode: (value: ThemeMode) => void };
const Context = createContext<Value | null>(null);
export function PreferencesProvider({ children }: PropsWithChildren) {
  const system = useColorScheme();
  const [preferences, setPreferences] = useState<Preferences>({ language: 'en', mode: 'light' });
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let active = true;
    void AsyncStorage.getItem(KEY).then(raw => {
      if (!raw || !active) return;
      const saved: unknown = JSON.parse(raw);
      if (typeof saved === 'object' && saved !== null && 'language' in saved && 'mode' in saved &&
        (saved.language === 'ar' || saved.language === 'en') && (saved.mode === 'light' || saved.mode === 'dark' || saved.mode === 'system')) {
        setPreferences({ language: saved.language, mode: saved.mode });
      }
    }).catch(() => { /* Fall back to defaults when storage is unavailable. */ }).finally(() => { if (active) setLoaded(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => { if (loaded) void AsyncStorage.setItem(KEY, JSON.stringify(preferences)).catch(() => {}); }, [preferences, loaded]);
  const isDark = preferences.mode === 'dark' || (preferences.mode === 'system' && system === 'dark');
  return <Context.Provider value={{ ...preferences, isDark, colors: isDark ? dark : light,
    setLanguage: language => setPreferences(p => ({ ...p, language })), setMode: mode => setPreferences(p => ({ ...p, mode })) }}>{children}</Context.Provider>;
}
export function usePreferences() {
  const context = useContext(Context);
  if (!context) throw new Error('PreferencesProvider is required');
  return context;
}
