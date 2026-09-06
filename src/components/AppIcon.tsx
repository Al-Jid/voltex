import Svg, { Path } from 'react-native-svg';
const paths = {
  home: 'M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z',
  sales: 'M4 20h16M6 16v-5m6 5V5m6 11V8',
  stock: 'm3 7 9-4 9 4-9 4Zm0 0v10l9 4 9-4V7M12 11v10M7 5l10 4',
  reward: 'M8 3h8v7a4 4 0 0 1-8 0ZM8 5H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4m-4 2v6m-4 1h8',
  more: 'M5 5h2v2H5Zm12 0h2v2h-2ZM5 17h2v2H5Zm12 0h2v2h-2Z',
  plus: 'M12 5v14M5 12h14', back: 'm14 5-7 7 7 7', next: 'm9 5 7 7-7 7',
  bell: 'M6 9a6 6 0 0 1 12 0c0 5 2 7 2 7H4s2-2 2-7m4 11h4',
  clock: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2',
  camera: 'M8 6 9 3h6l1 3h5v14H3V6Zm4 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
  request: 'M5 3h14v18H5ZM8 8h8M8 12h8M8 16h5',
  user: 'M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM4 21v-3a8 5 0 0 1 16 0v3',
  settings: 'M4 6h16M4 12h16M4 18h16M8 3v6m8 0v6m-6 0v6',
  book: 'M12 5C8 3 5 3 3 4v16c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-5-1-9 1Zm0 0v16',
  pin: 'M12 22S4 13 4 9a8 8 0 0 1 16 0c0 4-8 13-8 13Zm0-16a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z',
  check: 'm5 12 4 4L19 6', search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm5 12 6 6',
  logout: 'M9 3H3v18h6m6-15 6 6-6 6m-8-6h14', star: 'm12 2 3 7 7 1-5 5 1 7-6-4-6 4 1-7-5-5 7-1Z',
} as const;
export type AppIconName = keyof typeof paths;
export function AppIcon({ name, color, size = 22 }: { name: AppIconName; color: string; size?: number }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" accessible={false}><Path d={paths[name]} /></Svg>;
}
