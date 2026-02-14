import { Match } from '~/api/tba/read';

function escapeCSV(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function generateMatchCSV(matches: Match[]): string {
  const maxTeamsPerAlliance = Math.max(
    ...matches.map((m) => m.alliances.red.team_keys.length),
    ...matches.map((m) => m.alliances.blue.team_keys.length),
    3,
  );

  const teamHeaders = [];
  for (let i = 1; i <= maxTeamsPerAlliance; i++) {
    teamHeaders.push(`Red ${i}`, `Blue ${i}`);
  }

  const headers = [
    'Match',
    'Comp Level',
    'Set Number',
    'Match Number',
    ...teamHeaders,
    'Red Score',
    'Blue Score',
    'Winning Alliance',
  ];

  const rows = matches.map((match) => {
    const teamCols = [];
    for (let i = 0; i < maxTeamsPerAlliance; i++) {
      teamCols.push(
        match.alliances.red.team_keys[i]?.substring(3) ?? '',
        match.alliances.blue.team_keys[i]?.substring(3) ?? '',
      );
    }

    return [
      match.key,
      match.comp_level,
      String(match.set_number),
      String(match.match_number),
      ...teamCols,
      String(match.alliances.red.score),
      String(match.alliances.blue.score),
      match.winning_alliance,
    ];
  });

  const csvContent = [
    headers.map(escapeCSV).join(','),
    ...rows.map((row) => row.map(escapeCSV).join(',')),
  ].join('\n');

  return csvContent;
}

export function downloadCSV(csv: string, filename: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
