import { MAX_VIEWS, getNumViewsForLayout } from '~/lib/gameday/layouts';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import type { GamedayUrlState } from '~/lib/gameday/useGamedayUrlSync';

// State
export interface GamedayState {
  layoutId: number | null;
  /** Map from grid position to webcast ID */
  positionToWebcast: (string | null)[];
  chatSidebarVisible: boolean;
  currentChat: string;
  webcastsById: Record<string, WebcastWithMeta>;
}

export function createEmptyPositionArray(): (string | null)[] {
  return Array.from({ length: MAX_VIEWS }, () => null);
}

export const initialState: GamedayState = {
  layoutId: null,
  positionToWebcast: createEmptyPositionArray(),
  chatSidebarVisible: true,
  currentChat: 'funroboticsnetwork', // TODO: Pull this from some configurable source
  webcastsById: {},
};

// Actions
export type GamedayAction =
  | { type: 'SET_LAYOUT'; layoutId: number }
  | { type: 'SET_WEBCASTS'; webcasts: Record<string, WebcastWithMeta> }
  | { type: 'ADD_WEBCAST_AT_POSITION'; webcastId: string; position: number }
  | { type: 'REMOVE_WEBCAST'; webcastId: string }
  | { type: 'SWAP_POSITIONS'; position1: number; position2: number }
  | { type: 'RESET_WEBCASTS' }
  | { type: 'TOGGLE_CHAT_SIDEBAR' }
  | { type: 'SET_CURRENT_CHAT'; channel: string }
  | { type: 'RESTORE_URL_STATE'; urlState: GamedayUrlState };

// Reducer
export function gamedayReducer(
  state: GamedayState,
  action: GamedayAction,
): GamedayState {
  switch (action.type) {
    case 'SET_LAYOUT': {
      const numViews = getNumViewsForLayout(action.layoutId);
      // Trim webcasts that don't fit in the new layout
      const newPositionToWebcast = state.positionToWebcast.slice(0, numViews);
      // Pad with nulls if needed
      while (newPositionToWebcast.length < MAX_VIEWS) {
        newPositionToWebcast.push(null);
      }
      return {
        ...state,
        layoutId: action.layoutId,
        positionToWebcast: newPositionToWebcast,
      };
    }

    case 'SET_WEBCASTS': {
      // Validate positionToWebcast - remove any IDs that don't exist in the new webcasts
      const validPositionToWebcast = state.positionToWebcast.map((id) =>
        id !== null && action.webcasts[id] ? id : null,
      );

      return {
        ...state,
        webcastsById: action.webcasts,
        positionToWebcast: validPositionToWebcast,
      };
    }

    case 'ADD_WEBCAST_AT_POSITION': {
      if (state.layoutId === null) return state;

      const numViews = getNumViewsForLayout(state.layoutId);
      if (action.position < 0 || action.position >= numViews) return state;

      // Remove the webcast from any existing position first
      const newPositionToWebcast = state.positionToWebcast.map((id) =>
        id === action.webcastId ? null : id,
      );
      // Add to new position
      newPositionToWebcast[action.position] = action.webcastId;

      return {
        ...state,
        positionToWebcast: newPositionToWebcast,
      };
    }

    case 'REMOVE_WEBCAST': {
      return {
        ...state,
        positionToWebcast: state.positionToWebcast.map((id) =>
          id === action.webcastId ? null : id,
        ),
      };
    }

    case 'SWAP_POSITIONS': {
      const newPositionToWebcast = [...state.positionToWebcast];
      const temp = newPositionToWebcast[action.position1];
      newPositionToWebcast[action.position1] =
        newPositionToWebcast[action.position2];
      newPositionToWebcast[action.position2] = temp;
      return {
        ...state,
        positionToWebcast: newPositionToWebcast,
      };
    }

    case 'RESET_WEBCASTS': {
      return {
        ...state,
        positionToWebcast: createEmptyPositionArray(),
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

        // Restore webcasts at positions, clearing any beyond layout capacity
        const positionToWebcast = urlState.positionToWebcast.map((id, i) =>
          i < numViews ? id : null,
        );
        newState.positionToWebcast = positionToWebcast;
      }

      // Restore chat state
      newState.chatSidebarVisible = urlState.chatSidebarVisible;
      if (urlState.currentChat) {
        newState.currentChat = urlState.currentChat;
      }

      return newState;
    }

    default:
      return state;
  }
}
