import { Link } from '@tanstack/react-router';
import { useState } from 'react';

import ArrowsLeftRightIcon from '~icons/lucide/arrow-left-right';
import PanelsTopLeftIcon from '~icons/lucide/panels-top-left';
import VideoIcon from '~icons/lucide/video';
import XIcon from '~icons/lucide/x';

import { SwapPositionDialog } from '~/components/tba/gameday/SwapPositionDialog';
import { WebcastEmbed } from '~/components/tba/gameday/WebcastEmbed';
import { WebcastSelectorDialog } from '~/components/tba/gameday/WebcastSelectorDialog';
import { Button } from '~/components/ui/button';
import { useGameday } from '~/lib/gameday/context';
import { getNumViewsForLayout } from '~/lib/gameday/layouts';
import type { GamedayContent } from '~/lib/gameday/types';

export function VideoCell({
  position,
  content,
  gridArea,
}: {
  position: number;
  content: GamedayContent | null;
  gridArea: string;
}) {
  const [webcastDialogOpen, setWebcastDialogOpen] = useState(false);
  const [swapDialogOpen, setSwapDialogOpen] = useState(false);

  const {
    state,
    availableContent,
    removeContent,
    addContentAtPosition,
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

  const handleContentSelected = (contentId: string) => {
    addContentAtPosition(contentId, position);
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
      {content ? (
        <>
          {/* Content area */}
          <div className="flex-1 overflow-hidden">
            {content.type === 'webcast' ? (
              <WebcastEmbed webcast={content.webcast.webcast} />
            ) : (
              <content.component />
            )}
          </div>

          {/* Toolbar */}
          <div
            className="flex h-10 shrink-0 items-center gap-1 border-t
              border-neutral-800 bg-neutral-900 px-2"
          >
            <span className="mr-auto truncate text-sm text-white">
              {content.type === 'data-panel' || content.webcast.isSpecial ? (
                content.name
              ) : (
                <Link
                  to="/event/$eventKey"
                  params={{
                    eventKey: content.id.split('-').slice(0, -1).join('-'),
                  }}
                  className="truncate text-sm text-white hover:underline"
                >
                  {content.name}
                </Link>
              )}
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
              title="Change content"
            >
              {content.type === 'webcast' ? (
                <VideoIcon className="h-4 w-4" />
              ) : (
                <PanelsTopLeftIcon className="h-4 w-4" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-neutral-300 hover:bg-neutral-800
                hover:text-white"
              onClick={() => removeContent(content.id)}
              title="Remove content"
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
            disabled={availableContent.length === 0}
          >
            {availableContent.length > 0
              ? 'Select content'
              : 'No content available'}
          </Button>
        </div>
      )}

      {/* Dialogs */}
      <WebcastSelectorDialog
        open={webcastDialogOpen}
        onOpenChange={setWebcastDialogOpen}
        onContentSelected={handleContentSelected}
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
