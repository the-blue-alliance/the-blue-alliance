export function getDefaultTeleopComponentName(year: number): string {
  if (year == 2015) {
    return 'teleop_points';
  }

  if (year < 2026) {
    return 'teleopPoints';
  }

  return 'totalTeleopPoints';
}

export function getDefaultAutoComponentName(year: number): string {
  if (year == 2015) {
    return 'auto_points';
  }

  if (year < 2026) {
    return 'autoPoints';
  }

  return 'totalAutoPoints';
}

export function getDefaultTotalComponentName(year: number): string {
  if (year == 2015) {
    return 'total_points';
  }

  return 'totalPoints';
}
