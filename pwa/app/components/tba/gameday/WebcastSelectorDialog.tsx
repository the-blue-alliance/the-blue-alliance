import HelpCircleIcon from '~icons/lucide/help-circle';
import ListOrderedIcon from '~icons/lucide/list-ordered';
import VideoIcon from '~icons/lucide/video';
import VideoOffIcon from '~icons/lucide/video-off';

import { WebcastStatus } from '~/api/tba/read';
import { WebcastTypeIcon } from '~/components/tba/gameday/WebcastTypeIcon';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';
import { ScrollArea } from '~/components/ui/scroll-area';
import { Separator } from '~/components/ui/separator';
import { useGameday } from '~/lib/gameday/context';
import type { WebcastWithMeta } from '~/lib/gameday/types';

export function WebcastSelectorDialog({
  open,
  onOpenChange,
  onContentSelected,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onContentSelected: (contentId: string) => void;
}) {
  const { availableContent } = useGameday();
  const dataPanels = availableContent.filter(
    (content) => content.type === 'data-panel',
  );
  const availableWebcasts = availableContent
    .filter((content) => content.type === 'webcast')
    .map((content) => content.webcast);

  // Group webcasts by special vs regular, then by online/offline status
  const specialWebcasts = availableWebcasts.filter(
    (w) => w.isSpecial && w.webcast.status !== WebcastStatus.OFFLINE,
  );
  const offlineSpecialWebcasts = availableWebcasts.filter(
    (w) => w.isSpecial && w.webcast.status === WebcastStatus.OFFLINE,
  );
  const regularWebcasts = availableWebcasts.filter(
    (w) => !w.isSpecial && w.webcast.status !== WebcastStatus.OFFLINE,
  );
  const offlineRegularWebcasts = availableWebcasts.filter(
    (w) => !w.isSpecial && w.webcast.status === WebcastStatus.OFFLINE,
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent focusContentOnOpen className="max-w-md p-0">
        <DialogHeader className="border-b px-4 py-3">
          <DialogTitle>Select content</DialogTitle>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh]">
          {availableContent.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground">
              No content available
            </div>
          ) : (
            <div className="py-2">
              {dataPanels.length > 0 && (
                <>
                  <div
                    className="px-4 py-1.5 text-xs font-semibold tracking-wider
                      text-primary uppercase"
                  >
                    Data Panels
                  </div>
                  {dataPanels.map((panel) => (
                    <button
                      key={panel.id}
                      onClick={() => onContentSelected(panel.id)}
                      className="flex w-full cursor-pointer items-center gap-3
                        px-4 py-2 text-left transition-colors hover:bg-accent"
                    >
                      <ListOrderedIcon className="size-5 shrink-0" />
                      <span>{panel.name}</span>
                    </button>
                  ))}
                </>
              )}

              {/* Special Webcasts */}
              {specialWebcasts.length > 0 && (
                <>
                  {dataPanels.length > 0 && <Separator className="my-2" />}
                  <div
                    className="px-4 py-1.5 text-xs font-semibold tracking-wider
                      text-primary uppercase"
                  >
                    Special Webcasts
                  </div>
                  {specialWebcasts.map((webcast) => (
                    <WebcastItem
                      key={webcast.id}
                      webcast={webcast}
                      onClick={() => onContentSelected(webcast.id)}
                    />
                  ))}
                </>
              )}

              {/* Online Event Webcasts */}
              {regularWebcasts.length > 0 && (
                <>
                  {(dataPanels.length > 0 || specialWebcasts.length > 0) && (
                    <Separator className="my-2" />
                  )}
                  <div
                    className="px-4 py-1.5 text-xs font-semibold tracking-wider
                      text-primary uppercase"
                  >
                    Event Webcasts
                  </div>
                  {regularWebcasts.map((webcast) => (
                    <WebcastItem
                      key={webcast.id}
                      webcast={webcast}
                      onClick={() => onContentSelected(webcast.id)}
                    />
                  ))}
                </>
              )}

              {/* Offline Event Webcasts */}
              {offlineRegularWebcasts.length > 0 && (
                <>
                  {(dataPanels.length > 0 ||
                    specialWebcasts.length > 0 ||
                    regularWebcasts.length > 0) && (
                    <Separator className="my-2" />
                  )}
                  <div
                    className="px-4 py-1.5 text-xs font-semibold tracking-wider
                      text-muted-foreground uppercase"
                  >
                    Offline Event Webcasts
                  </div>
                  {offlineRegularWebcasts.map((webcast) => (
                    <WebcastItem
                      key={webcast.id}
                      webcast={webcast}
                      onClick={() => onContentSelected(webcast.id)}
                    />
                  ))}
                </>
              )}

              {/* Offline Special Webcasts */}
              {offlineSpecialWebcasts.length > 0 && (
                <>
                  {(dataPanels.length > 0 ||
                    specialWebcasts.length > 0 ||
                    regularWebcasts.length > 0 ||
                    offlineRegularWebcasts.length > 0) && (
                    <Separator className="my-2" />
                  )}
                  <div
                    className="px-4 py-1.5 text-xs font-semibold tracking-wider
                      text-muted-foreground uppercase"
                  >
                    Offline Special Webcasts
                  </div>
                  {offlineSpecialWebcasts.map((webcast) => (
                    <WebcastItem
                      key={webcast.id}
                      webcast={webcast}
                      onClick={() => onContentSelected(webcast.id)}
                    />
                  ))}
                </>
              )}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

function WebcastStatusIcon({ status }: { status?: WebcastStatus }) {
  if (status === WebcastStatus.ONLINE) {
    return <VideoIcon className="h-4 w-4 shrink-0 text-green-500" />;
  }
  if (status === WebcastStatus.OFFLINE) {
    return <VideoOffIcon className="h-4 w-4 shrink-0 text-muted-foreground" />;
  }
  return <HelpCircleIcon className="h-4 w-4 shrink-0 text-muted-foreground" />;
}

function WebcastItem({
  webcast,
  onClick,
}: {
  webcast: WebcastWithMeta;
  onClick: () => void;
}) {
  const status = webcast.webcast.status;

  // Secondary text: stream title for online streams
  const secondaryText =
    status === WebcastStatus.ONLINE && webcast.webcast.stream_title
      ? webcast.webcast.stream_title
      : null;

  return (
    <button
      onClick={onClick}
      className="flex w-full cursor-pointer items-center gap-3 px-4 py-2
        text-left transition-colors hover:bg-accent"
    >
      <WebcastTypeIcon
        type={webcast.webcast.type}
        className="h-5 w-5 shrink-0"
      />
      <div className="min-w-0 flex-1">
        <div className="truncate">{webcast.name}</div>
        {secondaryText && (
          <div className="truncate text-xs text-muted-foreground">
            {secondaryText}
          </div>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {/* Viewer count for online streams */}
        {status === WebcastStatus.ONLINE &&
          webcast.webcast.viewer_count != null && (
            <div className="text-right text-xs text-muted-foreground">
              <div>{webcast.webcast.viewer_count.toLocaleString()}</div>
              <div>Viewers</div>
            </div>
          )}
        <WebcastStatusIcon status={status} />
      </div>
    </button>
  );
}
