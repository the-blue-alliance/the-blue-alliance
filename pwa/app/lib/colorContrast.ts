import {
  formatHex,
  modeLrgb,
  modeOklab,
  modeOklch,
  modeRgb,
  parse,
  useMode as registerMode,
  toGamut,
  wcagContrast,
} from 'culori/fn';

registerMode(modeRgb);
registerMode(modeLrgb);
registerMode(modeOklab);
const toOklch = registerMode(modeOklch);
const toRgbGamut = toGamut('rgb', 'oklch');

export { wcagContrast };

export function parseColor(value: string): string | null {
  const color = parse(value.startsWith('#') ? value : `#${value}`);
  return color ? formatHex(color) : null;
}

export function nudgeLightness(
  hex: string,
  background: string,
  target = 3,
  maxDelta = 0.1,
): string {
  const color = toOklch(hex);
  const backdrop = toOklch(background);
  if (!color || !backdrop || wcagContrast(hex, background) >= target) {
    return hex;
  }
  const step = backdrop.l > 0.5 ? -0.01 : 0.01;
  let nudged = hex;
  for (let delta = step; Math.abs(delta) <= maxDelta + 1e-9; delta += step) {
    nudged = formatHex(toRgbGamut({ ...color, l: color.l + delta }));
    if (wcagContrast(nudged, background) >= target) break;
  }
  return nudged;
}
