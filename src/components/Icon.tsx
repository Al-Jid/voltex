import Svg, { Circle, Path, Rect } from 'react-native-svg';
export type IconName = 'globe' | 'chevron' | 'eye' | 'eyeOff' | 'check' | 'face' | 'fingerprint' | 'sun' | 'moon' | 'system' | 'close';
export function Icon({ name, size = 20, color = '#4D3BC1' }: { name: IconName; size?: number; color?: string }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" accessible={false}>
    {name === 'globe' && <><Circle cx="12" cy="12" r="9" /><Path d="M3 12h18M12 3c-5 5-5 13 0 18M12 3c5 5 5 13 0 18" /></>}
    {name === 'chevron' && <Path d="m8 10 4 4 4-4" />}
    {(name === 'eye' || name === 'eyeOff') && <><Path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><Circle cx="12" cy="12" r="3" />{name === 'eyeOff' && <Path d="m3 3 18 18" />}</>}
    {name === 'check' && <Path d="m5 12 4 4L19 6" />}
    {name === 'face' && <><Path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3M8 8v3m8-3v3m-4-2v5h-2m-2 3c2 2 6 2 8 0" /></>}
    {name === 'fingerprint' && <><Path d="M4 6c4-5 12-5 16 0M2 10c2-8 18-8 20 0M3 15v-3c0-11 18-11 18 0v3M6 18v-6c0-7 12-7 12 0v4c0 3 1 4 2 5M9 21c1-3 0-6 0-9 0-4 6-4 6 0v5c0 2 1 4 2 5M12 11v5c0 3 0 4-1 6M3 18l1 2" /></>}
    {name === 'sun' && <><Circle cx="12" cy="12" r="4" /><Path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></>}
    {name === 'moon' && <Path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z" />}
    {name === 'system' && <><Rect x="3" y="4" width="18" height="13" rx="2" /><Path d="M12 17v4m-4 0h8" /></>}
    {name === 'close' && <Path d="m6 6 12 12M6 18 18 6" />}
  </Svg>;
}
