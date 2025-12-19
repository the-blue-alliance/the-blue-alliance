import { createFileRoute } from '@tanstack/react-router';
import { useEffect, useState } from 'react';

import { Badge } from '~/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { getCacheEntries, getCacheStats } from '~/lib/middleware/network-cache';
import { publicCacheControlHeaders } from '~/lib/utils';

interface CacheInfo {
  key: string;
  method: string;
  url: string;
  dataPreview: string;
  remainingTTL: number;
  expiresAt: string;
}

const PREVIEW_JSON_LENGTH = 50;

export const Route = createFileRoute('/local/debug')({
  loader: () => {
    const stats = getCacheStats();
    const entries = getCacheEntries();
    const now = Date.now();

    // Parse cache entries to extract useful information
    const cacheEntries: CacheInfo[] = entries.map(
      ({ key, data, remainingTTL }) => {
        // Format: METHOD:URL
        const parts = key.split(':');
        const method = parts[0] || 'UNKNOWN';
        const url = parts.slice(1).join(':') || '';

        // Create preview of JSON data (first ~30 chars)
        const preview =
          data.length > PREVIEW_JSON_LENGTH
            ? data.substring(0, PREVIEW_JSON_LENGTH) + '...'
            : data;

        // Calculate expiry time
        const expiresAt = new Date(now + remainingTTL).toISOString();

        return {
          key,
          method,
          url,
          dataPreview: preview,
          remainingTTL,
          expiresAt,
        };
      },
    );

    return {
      stats,
      cacheEntries,
      timestamp: new Date().toISOString(),
    };
  },
  headers: publicCacheControlHeaders(),
  component: LocalDebug,
  head: () => {
    return {
      meta: [
        {
          title: 'Network Cache Debug - The Blue Alliance',
        },
        {
          name: 'description',
          content: 'Debug information about the network cache',
        },
      ],
    };
  },
});

function formatTimeRemaining(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}

function CacheEntryRow({
  entry,
  loadTime,
}: {
  entry: CacheInfo;
  loadTime: number;
}): React.JSX.Element {
  const [timeRemaining, setTimeRemaining] = useState(
    entry.remainingTTL - (Date.now() - loadTime),
  );

  useEffect(() => {
    const interval = setInterval(() => {
      const remaining = entry.remainingTTL - (Date.now() - loadTime);
      if (remaining <= 0) {
        setTimeRemaining(0);
        clearInterval(interval);
      } else {
        setTimeRemaining(remaining);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [entry.remainingTTL, loadTime]);

  const expiryDate = new Date(entry.expiresAt);

  return (
    <tr key={entry.key} className="border-b hover:bg-muted">
      <td className="px-4 py-2 font-mono text-sm">
        <Badge variant="outline">{entry.method}</Badge>
      </td>
      <td className="px-4 py-2 font-mono text-xs break-all">{entry.url}</td>
      <td className="px-4 py-2 font-mono text-xs break-all">
        {entry.dataPreview}
      </td>
      <td className="px-4 py-2 font-mono text-xs">
        <div>{formatTimeRemaining(timeRemaining)}</div>
        <div className="text-muted-foreground">
          {expiryDate.toLocaleString()}
        </div>
      </td>
    </tr>
  );
}

function LocalDebug(): React.JSX.Element {
  const loaderData = Route.useLoaderData();
  const { stats, cacheEntries, timestamp } = loaderData;
  const loadTime = Date.parse(timestamp);

  return (
    <div className="container max-w-6xl py-8">
      <h1 className="mb-4 text-3xl font-medium">Network Cache Debug</h1>

      <Card>
        <CardHeader>
          <CardTitle>Cache Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Cache Size</div>
              <div className="text-3xl font-bold">{stats.size}</div>
              <div className="text-sm text-muted-foreground">entries</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Max Entries</div>
              <div className="text-3xl font-bold">{stats.maxEntries}</div>
              <div className="text-sm text-muted-foreground">limit</div>
            </div>
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground">Cache Usage</div>
              <div className="text-3xl font-bold">
                {stats.maxEntries > 0
                  ? Math.round((stats.size / stats.maxEntries) * 100)
                  : 0}
                %
              </div>
              <div className="text-sm text-muted-foreground">capacity</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Last updated: {new Date(timestamp).toLocaleString()}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Cache Entries</CardTitle>
        </CardHeader>
        <CardContent>
          {cacheEntries.length === 0 ? (
            <p className="text-muted-foreground">No cache entries found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full table-auto border-collapse">
                <thead>
                  <tr className="border-b bg-neutral-50">
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Method
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      URL
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Data Preview
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      TTL
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {cacheEntries.map((entry) => (
                    <CacheEntryRow
                      key={entry.key}
                      entry={entry}
                      loadTime={loadTime}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
