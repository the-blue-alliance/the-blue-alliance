import { useState } from 'react';

import ClipboardCopyIcon from '~icons/lucide/clipboard-copy';
import DownloadIcon from '~icons/lucide/download';

import { Button } from '~/components/ui/button';
import { copyCsvToClipboard, downloadCsv } from '~/lib/csvUtils';

interface ScoutingExportProps {
  title: string;
  csvData: string;
  filename: string;
}

export default function ScoutingExport({
  title,
  csvData,
  filename,
}: ScoutingExportProps) {
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleCopy = async () => {
    try {
      await copyCsvToClipboard(csvData);
      showMessage('success', 'Copied to clipboard!');
    } catch (error) {
      if (error instanceof Error) {
        if (error.message.includes('not available')) {
          showMessage(
            'error',
            'Clipboard requires HTTPS. Use Download button.',
          );
        } else {
          showMessage(
            'error',
            'Clipboard access denied. Please use Download instead.',
          );
        }
      } else {
        showMessage('error', 'Failed to copy to clipboard.');
      }
    }
  };

  const handleDownload = () => {
    try {
      downloadCsv(csvData, filename);
      showMessage('success', 'Download started!');
    } catch {
      showMessage('error', 'Failed to download CSV.');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="flex gap-2">
          <Button
            onClick={() => {
              void handleCopy();
            }}
            variant="outline"
            size="sm"
          >
            <ClipboardCopyIcon className="mr-2 size-4" />
            Copy
          </Button>
          <Button onClick={handleDownload} size="sm">
            <DownloadIcon className="mr-2 size-4" />
            Download
          </Button>
        </div>
      </div>
      {message && (
        <div
          className={`text-sm font-medium ${
            message.type === 'success'
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          }`}
        >
          {message.text}
        </div>
      )}
      <textarea
        disabled
        value={csvData}
        className="w-full resize-y overflow-x-auto rounded-lg border
          border-border/50 bg-muted/30 p-4 font-mono text-xs whitespace-nowrap
          focus:outline-none"
        rows={12}
      />
    </div>
  );
}
