import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';

import { DATA_PANELS } from '~/lib/gameday/dataPanels';
import { getBestLayoutForCount } from '~/lib/gameday/layouts';
import {
  type GamedayState,
  gamedayReducer,
  initialState,
} from '~/lib/gameday/reducer';
import type { GamedayContent } from '~/lib/gameday/types';
import { useFirebaseWebcasts } from '~/lib/gameday/useFirebaseWebcasts';
import {
  hasUrlStateToRestore,
  useGamedayUrlSync,
} from '~/lib/gameday/useGamedayUrlSync';

const GamedayContext = createContext<{
  state: GamedayState;
  // Convenience selectors
  contentById: Record<string, GamedayContent>;
  availableContent: GamedayContent[];
  /** True while URL state is being restored (prevents flash of layout selector) */
  isInitializing: boolean;
  // Convenience actions
  setLayout: (layoutId: number) => void;
  addContentAtPosition: (contentId: string, position: number) => void;
  removeContent: (contentId: string) => void;
  swapPositions: (position1: number, position2: number) => void;
  resetContent: () => void;
  toggleChatSidebar: () => void;
  setCurrentChat: (channel: string) => void;
} | null>(null);

// Provider
export function GamedayProvider({
  children,
  initialEventCode,
}: {
  children: React.ReactNode;
  initialEventCode?: string;
}) {
  const [state, dispatch] = useReducer(gamedayReducer, initialState);

  // Track if we've loaded webcasts for the initial event code
  const hasLoadedEventWebcasts = useRef(false);

  // Subscribe to Firebase and sync webcasts into state
  const { webcasts: firebaseWebcasts, isLoading } = useFirebaseWebcasts();

  // URL sync hook
  const { initialUrlState } = useGamedayUrlSync({
    layoutId: state.layoutId,
    positionToContent: state.positionToContent,
    chatSidebarVisible: state.chatSidebarVisible,
    currentChat: state.currentChat,
  });

  // Check if we have URL state to restore (computed synchronously)
  const hasUrlState = hasUrlStateToRestore(initialUrlState);

  // We're initializing if restoring URL state, or if waiting for Firebase to
  // load webcasts for an event code (prevents flash of the layout selector)
  const isInitializing =
    (hasUrlState && !state.hasRestoredUrlState) ||
    (!!initialEventCode && isLoading && !hasUrlState);

  // Restore state from URL after webcasts are loaded (so webcast IDs are valid)
  useEffect(() => {
    if (!isLoading && !state.hasRestoredUrlState) {
      dispatch({ type: 'RESTORE_URL_STATE', urlState: initialUrlState });
    }
  }, [isLoading, state.hasRestoredUrlState, initialUrlState]);

  useEffect(() => {
    if (!isLoading) {
      dispatch({
        type: 'SET_WEBCASTS',
        webcasts: firebaseWebcasts,
        dataPanelIds: DATA_PANELS.map((panel) => panel.id),
      });
    }
  }, [firebaseWebcasts, isLoading]);

  // Auto-load all webcasts for the initial event code once Firebase is ready
  useEffect(() => {
    if (
      isLoading ||
      !initialEventCode ||
      hasLoadedEventWebcasts.current ||
      hasUrlStateToRestore(initialUrlState)
    )
      return;

    const eventWebcasts = Object.values(state.webcastsById)
      .filter((w) => !w.isSpecial && w.id.startsWith(`${initialEventCode}-`))
      .sort((a, b) => a.id.localeCompare(b.id));

    if (eventWebcasts.length === 0) return;

    hasLoadedEventWebcasts.current = true;
    const layoutId = getBestLayoutForCount(eventWebcasts.length);
    dispatch({
      type: 'LOAD_EVENT_WEBCASTS',
      webcasts: eventWebcasts,
      layoutId,
    });
  }, [isLoading, initialEventCode, state.webcastsById, initialUrlState]);

  // Selectors
  const displayedContent = useMemo(
    () => state.positionToContent.filter((id): id is string => id !== null),
    [state.positionToContent],
  );

  const contentById = useMemo<Record<string, GamedayContent>>(
    () => ({
      ...Object.fromEntries(
        Object.values(state.webcastsById).map((webcast) => [
          webcast.id,
          {
            type: 'webcast' as const,
            id: webcast.id,
            name: webcast.name,
            webcast,
          },
        ]),
      ),
      ...Object.fromEntries(DATA_PANELS.map((panel) => [panel.id, panel])),
    }),
    [state.webcastsById],
  );

  const availableContent = useMemo(() => {
    const displayedSet = new Set(displayedContent);
    return Object.values(contentById).filter(
      (content) => !displayedSet.has(content.id),
    );
  }, [contentById, displayedContent]);

  // Actions
  const setLayout = useCallback(
    (layoutId: number) => dispatch({ type: 'SET_LAYOUT', layoutId }),
    [],
  );

  const addContentAtPosition = useCallback(
    (contentId: string, position: number) =>
      dispatch({ type: 'ADD_CONTENT_AT_POSITION', contentId, position }),
    [],
  );

  const removeContent = useCallback(
    (contentId: string) => dispatch({ type: 'REMOVE_CONTENT', contentId }),
    [],
  );

  const swapPositions = useCallback(
    (position1: number, position2: number) =>
      dispatch({ type: 'SWAP_POSITIONS', position1, position2 }),
    [],
  );

  const resetContent = useCallback(
    () => dispatch({ type: 'RESET_CONTENT' }),
    [],
  );

  const toggleChatSidebar = useCallback(
    () => dispatch({ type: 'TOGGLE_CHAT_SIDEBAR' }),
    [],
  );

  const setCurrentChat = useCallback(
    (channel: string) => dispatch({ type: 'SET_CURRENT_CHAT', channel }),
    [],
  );

  const value = useMemo(
    () => ({
      state,
      contentById,
      availableContent,
      isInitializing,
      setLayout,
      addContentAtPosition,
      removeContent,
      swapPositions,
      resetContent,
      toggleChatSidebar,
      setCurrentChat,
    }),
    [
      state,
      contentById,
      availableContent,
      isInitializing,
      setLayout,
      addContentAtPosition,
      removeContent,
      swapPositions,
      resetContent,
      toggleChatSidebar,
      setCurrentChat,
    ],
  );

  return (
    <GamedayContext.Provider value={value}>{children}</GamedayContext.Provider>
  );
}

// Hook
export function useGameday() {
  const context = useContext(GamedayContext);
  if (!context) {
    throw new Error('useGameday must be used within a GamedayProvider');
  }
  return context;
}
