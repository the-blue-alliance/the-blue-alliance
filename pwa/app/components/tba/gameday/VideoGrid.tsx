import { useMemo } from 'react';

import { VideoCell } from '~/components/tba/gameday/VideoCell';
import { useGameday } from '~/lib/gameday/context';
import { getLayoutById } from '~/lib/gameday/layouts';

export function VideoGrid() {
  const { state } = useGameday();

  const layout = getLayoutById(state.layoutId);

  // Build a stable list of cells. We render cells with webcasts in a consistent
  // order (sorted by webcast ID) so that swapping positions only changes the
  // gridArea prop, not the array order. This prevents React from remounting
  // the video embeds.
  const cells = useMemo(() => {
    if (!layout) return [];

    // Build position-to-gridArea mapping
    const positionData: Array<{
      position: number;
      gridArea: string;
      webcastId: string | null;
    }> = [];

    for (let i = 0; i < layout.numViews; i++) {
      positionData.push({
        position: i,
        gridArea: layout.gridAreas[i],
        webcastId: state.positionToWebcast[i],
      });
    }

    // Separate into cells with webcasts and empty cells
    // Use type predicate to narrow webcastId to string (not null)
    const webcastCells = positionData.filter(
      (p): p is typeof p & { webcastId: string } => p.webcastId !== null,
    );
    const emptyCells = positionData.filter((p) => p.webcastId === null);

    // Sort webcast cells by webcast ID for stable ordering
    webcastCells.sort((a, b) => a.webcastId.localeCompare(b.webcastId));

    // Render webcast cells first (stable order), then empty cells (by position)
    const result: React.ReactNode[] = [];

    for (const cell of webcastCells) {
      const webcast = state.webcastsById[cell.webcastId];
      result.push(
        <VideoCell
          key={cell.webcastId}
          position={cell.position}
          webcast={webcast}
          gridArea={cell.gridArea}
        />,
      );
    }

    for (const cell of emptyCells) {
      result.push(
        <VideoCell
          key={`empty-${cell.position}`}
          position={cell.position}
          webcast={null}
          gridArea={cell.gridArea}
        />,
      );
    }

    return result;
  }, [layout, state.positionToWebcast, state.webcastsById]);

  if (!layout) return null;

  return (
    <div
      className="grid h-full w-full gap-0"
      style={{ gridTemplate: layout.gridTemplate }}
    >
      {cells}
    </div>
  );
}
