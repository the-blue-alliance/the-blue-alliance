import {
  formatHex,
  modeLrgb,
  modeOklch,
  modeRgb,
  parse,
  useMode as registerMode,
  wcagContrast,
} from 'culori/fn';

registerMode(modeRgb);
registerMode(modeLrgb);
registerMode(modeOklch);

export { wcagContrast };

export function parseColor(value: string): string | null {
  const color = parse(value.startsWith('#') ? value : `#${value}`);
  return color ? formatHex(color) : null;
}
