import { ChatSidebar } from '~/components/tba/gameday/ChatSidebar';
import { GamedayToolbar } from '~/components/tba/gameday/GamedayToolbar';
import { LayoutSelector } from '~/components/tba/gameday/LayoutSelector';
import { VideoGrid } from '~/components/tba/gameday/VideoGrid';
import { useGameday } from '~/lib/gameday/context';

export function GamedayFrame() {
  const { state, isInitializing } = useGameday();

  let mainContent;
  if (isInitializing) {
    // Don't show anything while restoring URL state to prevent flash of layout selector
    mainContent = null;
  } else if (state.layoutId === null) {
    mainContent = <LayoutSelector />;
  } else {
    mainContent = <VideoGrid />;
  }

  return (
    <div
      className="flex h-screen w-screen flex-col overflow-hidden bg-neutral-950"
    >
      <GamedayToolbar />

      <div className="flex min-h-0 flex-1">
        <div className="flex-1 overflow-hidden">{mainContent}</div>
        {state.layoutId !== null && <ChatSidebar />}
      </div>
    </div>
  );
}
