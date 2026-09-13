import { MAX_VIEWS, getNumViewsForLayout } from '~/lib/gameday/layouts';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import type { GamedayUrlState } from '~/lib/gameday/useGamedayUrlSync';

// State
export interface GamedayState {
  layoutId: number | null;
  /** Map from grid position to webcast or data-panel ID */
  positionToContent: (string | null)[];
  chatSidebarVisible: boolean;
  currentChat: string;
  webcastsById: Record<string, WebcastWithMeta>;
  hasRestoredUrlState: boolean;
}

export function createEmptyPositionArray(): (string | null)[] {
  return Array.from({ length: MAX_VIEWS }, () => null);
}

export const initialState: GamedayState = {
  layoutId: null,
  positionToContent: createEmptyPositionArray(),
  chatSidebarVisible: true,
  currentChat: 'funroboticsnetwork', // TODO: Pull this from some configurable source
  webcastsById: {},
  hasRestoredUrlState: false,
};

// Actions
export type GamedayAction =
  | { type: 'SET_LAYOUT'; layoutId: number }
  | {
      type: 'SET_WEBCASTS';
      webcasts: Record<string, WebcastWithMeta>;
      dataPanelIds?: readonly string[];
    }
  | { type: 'ADD_CONTENT_AT_POSITION'; contentId: string; position: number }
  | { type: 'REMOVE_CONTENT'; contentId: string }
  | { type: 'SWAP_POSITIONS'; position1: number; position2: number }
  | { type: 'RESET_CONTENT' }
  | { type: 'TOGGLE_CHAT_SIDEBAR' }
  | { type: 'SET_CURRENT_CHAT'; channel: string }
  | { type: 'RESTORE_URL_STATE'; urlState: GamedayUrlState }
  | {
      type: 'LOAD_EVENT_WEBCASTS';
      webcasts: WebcastWithMeta[];
      layoutId: number;
    };

// Reducer
export function gamedayReducer(
  state: GamedayState,
  action: GamedayAction,
): GamedayState {
  switch (action.type) {
    case 'SET_LAYOUT': {
      const numViews = getNumViewsForLayout(action.layoutId);
      // Trim content that doesn't fit in the new layout
      const newPositionToContent = state.positionToContent.slice(0, numViews);
      // Pad with nulls if needed
      while (newPositionToContent.length < MAX_VIEWS) {
        newPositionToContent.push(null);
      }
      return {
        ...state,
        layoutId: action.layoutId,
        positionToContent: newPositionToContent,
      };
    }

    case 'SET_WEBCASTS': {
      const validPositionToContent = state.positionToContent.map((id) => {
        const isAvailable =
          id !== null &&
          (action.webcasts[id] || action.dataPanelIds?.includes(id));
        return isAvailable ? id : null;
      });

      return {
        ...state,
        webcastsById: action.webcasts,
        positionToContent: validPositionToContent,
      };
    }

    case 'ADD_CONTENT_AT_POSITION': {
      if (state.layoutId === null) return state;

      const numViews = getNumViewsForLayout(state.layoutId);
      if (action.position < 0 || action.position >= numViews) return state;

      // Remove the content from any existing position first
      const newPositionToContent = state.positionToContent.map((id) =>
        id === action.contentId ? null : id,
      );
      // Add to new position
      newPositionToContent[action.position] = action.contentId;

      return {
        ...state,
        positionToContent: newPositionToContent,
      };
    }

    case 'REMOVE_CONTENT': {
      return {
        ...state,
        positionToContent: state.positionToContent.map((id) =>
          id === action.contentId ? null : id,
        ),
      };
    }

    case 'SWAP_POSITIONS': {
      const newPositionToContent = [...state.positionToContent];
      const temp = newPositionToContent[action.position1];
      newPositionToContent[action.position1] =
        newPositionToContent[action.position2];
      newPositionToContent[action.position2] = temp;
      return {
        ...state,
        positionToContent: newPositionToContent,
      };
    }

    case 'RESET_CONTENT': {
      return {
        ...state,
        positionToContent: createEmptyPositionArray(),
      };
    }

    case 'TOGGLE_CHAT_SIDEBAR': {
      return {
        ...state,
        chatSidebarVisible: !state.chatSidebarVisible,
      };
    }

    case 'SET_CURRENT_CHAT': {
      return {
        ...state,
        currentChat: action.channel,
      };
    }

    case 'RESTORE_URL_STATE': {
      const { urlState } = action;
      const newState = { ...state };

      // Restore layout if present in URL
      if (urlState.layoutId !== null) {
        const numViews = getNumViewsForLayout(urlState.layoutId);
        newState.layoutId = urlState.layoutId;

        // Restore content at positions, clearing any beyond layout capacity
        const positionToContent = urlState.positionToContent.map((id, i) =>
          i < numViews ? id : null,
        );
        newState.positionToContent = positionToContent;
      }

      // Restore chat state
      newState.chatSidebarVisible = urlState.chatSidebarVisible;
      if (urlState.currentChat) {
        newState.currentChat = urlState.currentChat;
      }

      newState.hasRestoredUrlState = true;
      return newState;
    }

    case 'LOAD_EVENT_WEBCASTS': {
      const { webcasts, layoutId } = action;
      const numViews = getNumViewsForLayout(layoutId);
      const positionToContent = createEmptyPositionArray();
      webcasts.slice(0, numViews).forEach((w, i) => {
        positionToContent[i] = w.id;
      });
      return {
        ...state,
        layoutId,
        positionToContent,
      };
    }

    default:
      return state;
  }
}
