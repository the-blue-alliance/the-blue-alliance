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
