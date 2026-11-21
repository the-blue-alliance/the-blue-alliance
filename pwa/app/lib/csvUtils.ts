export type DelimitedFormat = 'csv' | 'tsv';

interface GenerateCsvOptions {
  columns: string[];
  data: (string | number)[][];
  format?: DelimitedFormat;
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

export function escapeTsvField(value: string | number): string {
  return String(value).replace(/[\t\r\n]+/g, ' ');
}

export function generateCsv({
  columns,
  data,
  format = 'csv',
}: GenerateCsvOptions): string {
  const [escape, separator] =
    format === 'tsv' ? [escapeTsvField, '\t'] : [escapeCsvField, ','];
  const rows: string[] = [];

  const headerRow = columns.map(escape).join(separator);
  rows.push(headerRow);

  for (const row of data) {
    const csvRow = row.map(escape).join(separator);
    rows.push(csvRow);
  }

  return rows.join('\r\n');
}

export function downloadCsv(
  csv: string,
  filename: string,
  format: DelimitedFormat = 'csv',
): void {
  const mimeType = format === 'tsv' ? 'text/tab-separated-values' : 'text/csv';
  const blob = new Blob([csv], { type: `${mimeType};charset=utf-8;` });
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
