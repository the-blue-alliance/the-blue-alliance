import { toast } from 'sonner';

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
  const handleCopy = async () => {
    try {
      await copyCsvToClipboard(csvData);
      toast.success('Copied to clipboard!');
    } catch (error) {
      if (error instanceof Error) {
        if (error.message.includes('not available')) {
          toast.error('Clipboard requires HTTPS. Use Download button.');
        } else {
          toast.error('Clipboard access denied. Please use Download instead.');
        }
      } else {
        toast.error('Failed to copy to clipboard.');
      }
    }
  };

  const handleDownload = () => {
    try {
      downloadCsv(csvData, filename);
      toast.success('Download started!');
    } catch {
      toast.error('Failed to download CSV.');
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
