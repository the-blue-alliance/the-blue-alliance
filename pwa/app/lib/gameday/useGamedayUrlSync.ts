import { useNavigate, useSearch } from '@tanstack/react-router';
import { useEffect, useRef } from 'react';

import { MAX_VIEWS } from '~/lib/gameday/layouts';
import type { GamedaySearchParams } from '~/routes/gameday';

/**
 * State values that get persisted to URL
 */
export interface GamedayUrlState {
  layoutId: number | null;
  positionToWebcast: (string | null)[];
  chatSidebarVisible: boolean;
  currentChat: string;
}

/**
 * Check if URL state has any meaningful values to restore
 */
export function hasUrlStateToRestore(urlState: GamedayUrlState): boolean {
  return (
    urlState.layoutId !== null ||
    urlState.positionToWebcast.some((id) => id !== null) ||
    urlState.currentChat !== '' ||
    !urlState.chatSidebarVisible
  );
}

/**
 * Parse URL search params into gameday state
 */
export function parseSearchParams(
  searchParams: GamedaySearchParams,
): GamedayUrlState {
  // Layout (already parsed as number by zod schema)
  const layoutId = searchParams.layout ?? null;

  // Webcast positions: view_0, view_1, ... view_N
  const positionToWebcast: (string | null)[] = Array.from(
    { length: MAX_VIEWS },
    () => null,
  );
  for (let i = 0; i < MAX_VIEWS; i++) {
    const viewParam = searchParams[`view_${i}` as keyof GamedaySearchParams] as
      | string
      | undefined;
    if (viewParam) {
      positionToWebcast[i] = viewParam;
    }
  }

  // Chat sidebar
  const chatParam = searchParams.chat;
  const chatSidebarVisible = chatParam !== 'hidden';
  const currentChat = chatParam === 'hidden' ? '' : (chatParam ?? '');

  return {
    layoutId,
    positionToWebcast,
    chatSidebarVisible,
    currentChat,
  };
}

/**
 * Serialize gameday state to URL search params
 */
export function serializeToSearchParams(
  state: GamedayUrlState,
): GamedaySearchParams {
  const params: GamedaySearchParams = {};

  // Layout
  if (state.layoutId !== null) {
    params.layout = state.layoutId;
  }

  // Webcast positions
  for (let i = 0; i < state.positionToWebcast.length; i++) {
    const webcastId = state.positionToWebcast[i];
    if (webcastId) {
      (params as Record<string, unknown>)[`view_${i}`] = webcastId;
    }
  }

  // Chat
  if (state.chatSidebarVisible) {
    if (state.currentChat) {
      params.chat = state.currentChat;
    }
  } else {
    params.chat = 'hidden';
  }

  return params;
}

/**
 * Hook to synchronize gameday state with URL search params
 *
 * Returns initial state parsed from URL, and syncs state changes back to URL
 */
export function useGamedayUrlSync(state: {
  layoutId: number | null;
  positionToWebcast: (string | null)[];
  chatSidebarVisible: boolean;
  currentChat: string;
}) {
  const searchParams = useSearch({ from: '/gameday' });
  const navigate = useNavigate({ from: '/gameday' });
  const isInitialMount = useRef(true);
  const lastSerializedRef = useRef<string>('');

  // Parse URL params once on first render
  const initialUrlStateRef = useRef<GamedayUrlState | null>(null);
  if (initialUrlStateRef.current === null) {
    initialUrlStateRef.current = parseSearchParams(searchParams);
  }

  // Sync state to URL on changes
  useEffect(() => {
    // Skip the initial mount - we don't want to overwrite URL params before
    // the state has been restored from them
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    const urlState: GamedayUrlState = {
      layoutId: state.layoutId,
      positionToWebcast: state.positionToWebcast,
      chatSidebarVisible: state.chatSidebarVisible,
      currentChat: state.currentChat,
    };

    const newParams = serializeToSearchParams(urlState);
    const serialized = JSON.stringify(newParams);

    // Only update if actually changed to avoid infinite loops
    if (serialized !== lastSerializedRef.current) {
      lastSerializedRef.current = serialized;
      void navigate({
        search: newParams,
        replace: true,
        resetScroll: false,
      });
    }
  }, [
    state.layoutId,
    state.positionToWebcast,
    state.chatSidebarVisible,
    state.currentChat,
    navigate,
  ]);

  return { initialUrlState: initialUrlStateRef.current };
}
