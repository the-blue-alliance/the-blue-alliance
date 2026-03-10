export function getDefaultTeleopComponentName(year: number): string {
  if (year < 2026) {
    return 'teleopPoints';
  }

  return 'totalTeleopPoints';
}

export function getDefaultAutoComponentName(year: number): string {
  if (year < 2026) {
    return 'autoPoints';
  }

  return 'totalAutoPoints';
}
