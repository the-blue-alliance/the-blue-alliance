const DISTRICT_COLOR_BORDER_CLASSES: Record<string, string> = {
  ca: 'border-l-district-ca',
  chs: 'border-l-district-chs',
  fch: 'border-l-district-chs',
  fin: 'border-l-district-fin',
  in: 'border-l-district-fin',
  isr: 'border-l-district-isr',
  fim: 'border-l-district-fim',
  fma: 'border-l-district-fma',
  mar: 'border-l-district-fma',
  ne: 'border-l-district-ne',
  fnc: 'border-l-district-fnc',
  ont: 'border-l-district-ont',
  pnw: 'border-l-district-pnw',
  pch: 'border-l-district-pch',
  fsc: 'border-l-district-fsc',
  fit: 'border-l-district-fit',
  tx: 'border-l-district-fit',
  win: 'border-l-district-win',
};

export function getDistrictColorBorderClass(
  districtAbbreviation: string | undefined,
): string {
  if (!districtAbbreviation) return '';
  return (
    DISTRICT_COLOR_BORDER_CLASSES[districtAbbreviation.toLowerCase()] ?? ''
  );
}

// Inset box-shadow variant of the district stripe, for table rows that scroll
// beneath a sticky header (collapsed table borders paint over sticky cells).
// Full class names are spelled out so Tailwind can detect them.
const DISTRICT_COLOR_SHADOW_CLASSES: Record<string, string> = {
  ca: 'shadow-[inset_4px_0_0_0_var(--color-district-ca)]',
  chs: 'shadow-[inset_4px_0_0_0_var(--color-district-chs)]',
  fch: 'shadow-[inset_4px_0_0_0_var(--color-district-chs)]',
  fin: 'shadow-[inset_4px_0_0_0_var(--color-district-fin)]',
  in: 'shadow-[inset_4px_0_0_0_var(--color-district-fin)]',
  isr: 'shadow-[inset_4px_0_0_0_var(--color-district-isr)]',
  fim: 'shadow-[inset_4px_0_0_0_var(--color-district-fim)]',
  fma: 'shadow-[inset_4px_0_0_0_var(--color-district-fma)]',
  mar: 'shadow-[inset_4px_0_0_0_var(--color-district-fma)]',
  ne: 'shadow-[inset_4px_0_0_0_var(--color-district-ne)]',
  fnc: 'shadow-[inset_4px_0_0_0_var(--color-district-fnc)]',
  ont: 'shadow-[inset_4px_0_0_0_var(--color-district-ont)]',
  pnw: 'shadow-[inset_4px_0_0_0_var(--color-district-pnw)]',
  pch: 'shadow-[inset_4px_0_0_0_var(--color-district-pch)]',
  fsc: 'shadow-[inset_4px_0_0_0_var(--color-district-fsc)]',
  fit: 'shadow-[inset_4px_0_0_0_var(--color-district-fit)]',
  tx: 'shadow-[inset_4px_0_0_0_var(--color-district-fit)]',
  win: 'shadow-[inset_4px_0_0_0_var(--color-district-win)]',
};

export function getDistrictColorShadowClass(
  districtAbbreviation: string | undefined,
): string {
  if (!districtAbbreviation) return '';
  return (
    DISTRICT_COLOR_SHADOW_CLASSES[districtAbbreviation.toLowerCase()] ?? ''
  );
}
