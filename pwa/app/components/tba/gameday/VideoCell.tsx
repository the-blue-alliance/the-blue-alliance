import { useState } from 'react';

import ArrowsLeftRightIcon from '~icons/lucide/arrow-left-right';
import VideoIcon from '~icons/lucide/video';
import XIcon from '~icons/lucide/x';

import { SwapPositionDialog } from '~/components/tba/gameday/SwapPositionDialog';
import { WebcastEmbed } from '~/components/tba/gameday/WebcastEmbed';
import { WebcastSelectorDialog } from '~/components/tba/gameday/WebcastSelectorDialog';
import { Button } from '~/components/ui/button';
import { useGameday } from '~/lib/gameday/context';
import { getNumViewsForLayout } from '~/lib/gameday/layouts';
import type { WebcastWithMeta } from '~/lib/gameday/types';

export function VideoCell({
  position,
  webcast,
  gridArea,
}: {
  position: number;
  webcast: WebcastWithMeta | null;
  gridArea: string;
}) {
  const [webcastDialogOpen, setWebcastDialogOpen] = useState(false);
  const [swapDialogOpen, setSwapDialogOpen] = useState(false);

  const {
    state,
    availableWebcasts,
    removeWebcast,
    addWebcastAtPosition,
    swapPositions,
  } = useGameday();

  const handleSwapClick = () => {
    if (state.layoutId === null) return;
    const numViews = getNumViewsForLayout(state.layoutId);
    if (numViews === 2) {
      // Simple swap for 2-view layouts
      swapPositions(0, 1);
    } else {
      setSwapDialogOpen(true);
    }
  };

  const handleWebcastSelected = (webcastId: string) => {
    addWebcastAtPosition(webcastId, position);
    setWebcastDialogOpen(false);
  };

  const handleSwapPosition = (targetPosition: number) => {
    swapPositions(position, targetPosition);
    setSwapDialogOpen(false);
  };

  return (
    <div
      className="relative flex flex-col border border-neutral-700
        bg-neutral-950"
      style={{ gridArea }}
    >
      {webcast ? (
        <>
          {/* Video embed area */}
          <div className="flex-1 overflow-hidden">
            <WebcastEmbed webcast={webcast.webcast} />
          </div>

          {/* Toolbar */}
          <div
            className="flex h-10 shrink-0 items-center gap-1 border-t
              border-neutral-800 bg-neutral-900 px-2"
          >
            <span className="mr-auto truncate text-sm text-white">
              {webcast.name}
            </span>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-neutral-300 hover:bg-neutral-800
                hover:text-white"
              onClick={handleSwapClick}
              title="Swap position"
            >
              <ArrowsLeftRightIcon className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-neutral-300 hover:bg-neutral-800
                hover:text-white"
              onClick={() => setWebcastDialogOpen(true)}
              title="Change webcast"
            >
              <VideoIcon className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-neutral-300 hover:bg-neutral-800
                hover:text-white"
              onClick={() => removeWebcast(webcast.id)}
              title="Remove webcast"
            >
              <XIcon className="h-4 w-4" />
            </Button>
          </div>
        </>
      ) : (
        // Empty cell
        <div className="flex flex-1 items-center justify-center">
          <Button
            variant="secondary"
            className="cursor-pointer"
            onClick={() => setWebcastDialogOpen(true)}
            disabled={availableWebcasts.length === 0}
          >
            {availableWebcasts.length > 0
              ? 'Select a webcast'
              : 'No webcasts available'}
          </Button>
        </div>
      )}

      {/* Dialogs */}
      <WebcastSelectorDialog
        open={webcastDialogOpen}
        onOpenChange={setWebcastDialogOpen}
        onWebcastSelected={handleWebcastSelected}
      />

      <SwapPositionDialog
        open={swapDialogOpen}
        onOpenChange={setSwapDialogOpen}
        currentPosition={position}
        onPositionSelected={handleSwapPosition}
      />
    </div>
  );
}
