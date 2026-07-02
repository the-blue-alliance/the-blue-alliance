import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';

import { getBestLayoutForCount } from '~/lib/gameday/layouts';
import {
  type GamedayState,
  gamedayReducer,
  initialState,
} from '~/lib/gameday/reducer';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import { useFirebaseWebcasts } from '~/lib/gameday/useFirebaseWebcasts';
import {
  hasUrlStateToRestore,
  useGamedayUrlSync,
} from '~/lib/gameday/useGamedayUrlSync';

const GamedayContext = createContext<{
  state: GamedayState;
  // Convenience selectors
  availableWebcasts: WebcastWithMeta[];
  /** True while URL state is being restored (prevents flash of layout selector) */
  isInitializing: boolean;
  // Convenience actions
  setLayout: (layoutId: number) => void;
  addWebcastAtPosition: (webcastId: string, position: number) => void;
  removeWebcast: (webcastId: string) => void;
  swapPositions: (position1: number, position2: number) => void;
  resetWebcasts: () => void;
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

  // Track if we've restored URL state
  const hasRestoredUrlState = useRef(false);
  // Track if we've loaded webcasts for the initial event code
  const hasLoadedEventWebcasts = useRef(false);

  // Subscribe to Firebase and sync webcasts into state
  const { webcasts: firebaseWebcasts, isLoading } = useFirebaseWebcasts();

  // URL sync hook
  const { initialUrlState } = useGamedayUrlSync({
    layoutId: state.layoutId,
    positionToWebcast: state.positionToWebcast,
    chatSidebarVisible: state.chatSidebarVisible,
    currentChat: state.currentChat,
  });

  // Check if we have URL state to restore (computed synchronously)
  const hasUrlState = hasUrlStateToRestore(initialUrlState);

  // We're initializing if restoring URL state, or if waiting for Firebase to
  // load webcasts for an event code (prevents flash of the layout selector)
  const isInitializing =
    (hasUrlState && !hasRestoredUrlState.current) ||
    (!!initialEventCode && isLoading && !hasUrlState);

  // Restore state from URL after webcasts are loaded (so webcast IDs are valid)
  useEffect(() => {
    if (!isLoading && !hasRestoredUrlState.current) {
      hasRestoredUrlState.current = true;

      // Only restore if there's something to restore
      if (hasUrlStateToRestore(initialUrlState)) {
        dispatch({ type: 'RESTORE_URL_STATE', urlState: initialUrlState });
      }
    }
  }, [isLoading, initialUrlState]);

  useEffect(() => {
    if (!isLoading) {
      dispatch({
        type: 'SET_WEBCASTS',
        webcasts: firebaseWebcasts,
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
  const displayedWebcasts = useMemo(
    () => state.positionToWebcast.filter((id): id is string => id !== null),
    [state.positionToWebcast],
  );

  const availableWebcasts = useMemo(() => {
    const displayedSet = new Set(displayedWebcasts);
    return Object.values(state.webcastsById).filter(
      (w) => !displayedSet.has(w.id),
    );
  }, [state.webcastsById, displayedWebcasts]);

  // Actions
  const setLayout = useCallback(
    (layoutId: number) => dispatch({ type: 'SET_LAYOUT', layoutId }),
    [],
  );

  const addWebcastAtPosition = useCallback(
    (webcastId: string, position: number) =>
      dispatch({ type: 'ADD_WEBCAST_AT_POSITION', webcastId, position }),
    [],
  );

  const removeWebcast = useCallback(
    (webcastId: string) => dispatch({ type: 'REMOVE_WEBCAST', webcastId }),
    [],
  );

  const swapPositions = useCallback(
    (position1: number, position2: number) =>
      dispatch({ type: 'SWAP_POSITIONS', position1, position2 }),
    [],
  );

  const resetWebcasts = useCallback(
    () => dispatch({ type: 'RESET_WEBCASTS' }),
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
      availableWebcasts,
      isInitializing,
      setLayout,
      addWebcastAtPosition,
      removeWebcast,
      swapPositions,
      resetWebcasts,
      toggleChatSidebar,
      setCurrentChat,
    }),
    [
      state,
      availableWebcasts,
      isInitializing,
      setLayout,
      addWebcastAtPosition,
      removeWebcast,
      swapPositions,
      resetWebcasts,
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
