interface GenerateCsvOptions {
  columns: string[];
  data: (string | number)[][];
}

export function escapeCsvField(value: string | number): string {
  const strValue = String(value);

  if (
    strValue.includes(',') ||
    strValue.includes('"') ||
    strValue.includes('\n') ||
    strValue.includes('\r')
  ) {
    const escaped = strValue.replace(/"/g, '""');
    return `"${escaped}"`;
  }

  return strValue;
}

export function generateCsv({ columns, data }: GenerateCsvOptions): string {
  const rows: string[] = [];

  const headerRow = columns.map(escapeCsvField).join(',');
  rows.push(headerRow);

  for (const row of data) {
    const csvRow = row.map(escapeCsvField).join(',');
    rows.push(csvRow);
  }

  return rows.join('\r\n');
}

export function downloadCsv(csv: string, filename: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}

export async function copyCsvToClipboard(csv: string): Promise<void> {
  if (!navigator.clipboard) {
    throw new Error(
      'Clipboard API not available. Use HTTPS or download instead.',
    );
  }

  await navigator.clipboard.writeText(csv);
}
