// Adjusts team colors so chart marks stay visible on the chart background,
// keeping each color's hue and changing only its OKLCH lightness (chroma is
// reduced only where the lighter/darker color would fall outside sRGB).

type Rgb = [number, number, number];
type Oklch = [number, number, number];

// WCAG 2.x non-text contrast minimum for graphical objects (SC 1.4.11).
export const MIN_MARK_CONTRAST = 3;

// The chart sits on a Card; keep in sync with --card in app/style/theme.css.
export const CARD_BACKGROUND: { light: Oklch; dark: Oklch } = {
  light: [1, 0, 0],
  dark: [0.287, 0.004, 286.09],
};

function srgbToLinear(c: number): number {
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function linearToSrgb(c: number): number {
  return c <= 0.0031308 ? c * 12.92 : 1.055 * c ** (1 / 2.4) - 0.055;
}

function parseHex(hex: string): Rgb | null {
  const match = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(hex.trim());
  if (!match) return null;
  const digits =
    match[1].length === 3
      ? match[1]
          .split('')
          .map((d) => d + d)
          .join('')
      : match[1];
  return [0, 2, 4].map(
    (i) => parseInt(digits.slice(i, i + 2), 16) / 255,
  ) as Rgb;
}

function toHex(rgb: Rgb): string {
  return (
    '#' +
    rgb
      .map((c) =>
        Math.round(Math.min(1, Math.max(0, c)) * 255)
          .toString(16)
          .padStart(2, '0'),
      )
      .join('')
  );
}

function linearRgbToOklch([r, g, b]: Rgb): Oklch {
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  const L = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s;
  const a = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s;
  const bb = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s;
  return [L, Math.hypot(a, bb), Math.atan2(bb, a)];
}

function oklchToLinearRgb([L, C, h]: Oklch): Rgb {
  const a = C * Math.cos(h);
  const b = C * Math.sin(h);
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
}

function inGamut(rgb: Rgb): boolean {
  return rgb.every((c) => c >= -1e-6 && c <= 1 + 1e-6);
}

// Highest-chroma sRGB color at this lightness and hue, up to the given chroma.
function gamutMappedHex(L: number, C: number, h: number): string {
  let rgb = oklchToLinearRgb([L, C, h]);
  if (!inGamut(rgb)) {
    let lo = 0;
    let hi = C;
    for (let i = 0; i < 24; i++) {
      const mid = (lo + hi) / 2;
      if (inGamut(oklchToLinearRgb([L, mid, h]))) lo = mid;
      else hi = mid;
    }
    rgb = oklchToLinearRgb([L, lo, h]);
  }
  return toHex(rgb.map(linearToSrgb) as Rgb);
}

function luminance(linear: Rgb): number {
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function hexLuminance(hex: string): number {
  return luminance((parseHex(hex) ?? [0, 0, 0]).map(srgbToLinear) as Rgb);
}

export function contrastRatio(hex: string, background: Oklch): number {
  const a = hexLuminance(hex);
  const b = luminance(
    oklchToLinearRgb([
      background[0],
      background[1],
      (background[2] * Math.PI) / 180,
    ]),
  );
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/**
 * Returns `hex` unchanged if it already has 3:1 contrast with `background`;
 * otherwise the closest color of the same hue (lighter on a dark background,
 * darker on a light one) that does. Returns null for unparseable input.
 */
export function readableColorOn(hex: string, background: Oklch): string | null {
  const rgb = parseHex(hex);
  if (!rgb) return null;
  const normalized = toHex(rgb);
  if (contrastRatio(normalized, background) >= MIN_MARK_CONTRAST) {
    return normalized;
  }

  const [L, rawC, h] = linearRgbToOklch(rgb.map(srgbToLinear) as Rgb);
  // Grays have no meaningful hue; keep them neutral.
  const C = rawC < 1e-4 ? 0 : rawC;
  const lighten = background[0] < 0.5;
  // Search for the smallest lightness change that reaches the target.
  let near = L;
  let far = lighten ? 1 : 0;
  for (let i = 0; i < 24; i++) {
    const mid = (near + far) / 2;
    if (
      contrastRatio(gamutMappedHex(mid, C, h), background) >= MIN_MARK_CONTRAST
    )
      far = mid;
    else near = mid;
  }
  return gamutMappedHex(far, C, h);
}

/** Team color variants that stay visible on the chart card in each theme. */
export function readableTeamColors(
  hex: string,
): { light: string; dark: string } | null {
  const light = readableColorOn(hex, CARD_BACKGROUND.light);
  const dark = readableColorOn(hex, CARD_BACKGROUND.dark);
  return light && dark ? { light, dark } : null;
}
