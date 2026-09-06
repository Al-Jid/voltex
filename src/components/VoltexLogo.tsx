import Svg, { G, Path, Text as SvgText } from 'react-native-svg';

/** Hand-drawn vector reconstruction from the supplied raster reference. */
export function VoltexLogo({ dark = false }: { dark?: boolean }) {
  return <Svg width={164} height={43} viewBox="0 0 200 52" accessibilityRole="image" accessibilityLabel="VOLTEX — Powering Performance">
    <G fill={dark ? '#AD9BFF' : '#4D3BC1'} transform="translate(5 8) skewX(-12)">
      <Path d="M0 0h9l5 18L23 0h10L18 27H8Z" />
      <Path fillRule="evenodd" d="M45 0c-10 0-16 5-16 14s6 14 16 14 16-5 16-14S55 0 45 0Zm0 8c4 0 6 2 6 6s-2 6-6 6-6-2-6-6 2-6 6-6Z" />
      <Path d="M65 0h10v19h16v8H65ZM86 0h31v8h-10v19H97V8H86ZM120 0h27v7h-17v3h14v7h-14v3h17v7h-27Z" />
    </G>
    <Path transform="translate(24 0)" fill="#AD2530" d="M132 0h15l6 10 8-10h15l-17 21 12 22h-16l-6-12-10 12h-16l20-23Z" />
    <SvgText x="8" y="44" fontSize="5.6" fill={dark ? '#C0B8CF' : '#77717D'}>Powering Performance</SvgText>
  </Svg>;
}
