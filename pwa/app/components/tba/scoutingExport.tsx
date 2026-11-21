import { cn } from 'cn';
import { useId, useState } from 'react';
import { toast } from 'sonner';

import ChevronRightIcon from '~icons/lucide/chevron-right';
import ClipboardCopyIcon from '~icons/lucide/clipboard-copy';
import DownloadIcon from '~icons/lucide/download';

import { Button } from '~/components/ui/button';
import {
  type DelimitedFormat,
  copyCsvToClipboard,
  downloadCsv,
} from '~/lib/csvUtils';

interface ScoutingExportProps {
  title: string;
  description: string;
  rowCount: number;
  csvData: string;
  filename: string;
  format: DelimitedFormat;
}

export default function ScoutingExport({
  title,
  description,
  rowCount,
  csvData,
  filename,
  format,
}: ScoutingExportProps) {
  const [showPreview, setShowPreview] = useState(false);
  const previewId = useId();

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
      downloadCsv(csvData, filename, format);
      toast.success('Download started!');
    } catch {
      toast.error('Failed to download file.');
    }
  };

  return (
    <li className="space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">
            {description} · {rowCount} {rowCount === 1 ? 'row' : 'rows'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            aria-expanded={showPreview}
            aria-controls={previewId}
            onClick={() => setShowPreview(!showPreview)}
          >
            <ChevronRightIcon
              className={cn(
                'mr-1 size-4 motion-safe:transition-transform',
                showPreview && 'rotate-90',
              )}
            />
            Preview
          </Button>
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
      {showPreview && (
        <textarea
          id={previewId}
          readOnly
          aria-label={`${title} preview`}
          value={csvData}
          className="w-full resize-y overflow-x-auto rounded-lg border
            border-border/50 bg-muted/30 p-3 font-mono text-xs whitespace-pre
            tab-4 text-muted-foreground"
          rows={8}
        />
      )}
    </li>
  );
}
