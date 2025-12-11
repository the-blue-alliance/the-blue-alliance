import { describe, expect, test } from 'vitest';

import { MAX_VIEWS } from '~/lib/gameday/layouts';
import {
  type GamedayAction,
  type GamedayState,
  createEmptyPositionArray,
  gamedayReducer,
  initialState,
} from '~/lib/gameday/reducer';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import type { GamedayUrlState } from '~/lib/gameday/useGamedayUrlSync';

function createMockWebcast(id: string): WebcastWithMeta {
  return {
    id,
    name: `Webcast ${id}`,
    webcast: {
      type: 'twitch',
      channel: `channel-${id}`,
    },
    isSpecial: false,
  };
}

describe.concurrent('createEmptyPositionArray', () => {
  test('creates array with MAX_VIEWS null elements', () => {
    const arr = createEmptyPositionArray();
    expect(arr).toHaveLength(MAX_VIEWS);
    expect(arr.every((el) => el === null)).toBe(true);
  });

  test('creates independent arrays on each call', () => {
    const arr1 = createEmptyPositionArray();
    const arr2 = createEmptyPositionArray();
    arr1[0] = 'test';
    expect(arr2[0]).toBeNull();
  });
});

describe.concurrent('initialState', () => {
  test('has expected default values', () => {
    expect(initialState.layoutId).toBeNull();
    expect(initialState.positionToWebcast).toHaveLength(MAX_VIEWS);
    expect(initialState.chatSidebarVisible).toBe(true);
    expect(initialState.currentChat).toBe('funroboticsnetwork');
    expect(initialState.webcastsById).toEqual({});
  });
});

describe.concurrent('SET_LAYOUT action', () => {
  test('sets layout id', () => {
    const state = gamedayReducer(initialState, {
      type: 'SET_LAYOUT',
      layoutId: 3,
    });
    expect(state.layoutId).toBe(3);
  });

  test('preserves webcasts within new layout capacity', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      layoutId: 8, // 9 views
      positionToWebcast: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
    };

    // Switch to quad view (4 views)
    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SET_LAYOUT',
      layoutId: 3,
    });
    expect(state.positionToWebcast.slice(0, 4)).toEqual(['a', 'b', 'c', 'd']);
  });

  test('pads with nulls when switching to larger layout', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      layoutId: 0, // 1 view
      positionToWebcast: ['a', null, null, null, null, null, null, null, null],
    };

    // Switch to quad view (4 views)
    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SET_LAYOUT',
      layoutId: 3,
    });
    expect(state.positionToWebcast).toHaveLength(MAX_VIEWS);
    expect(state.positionToWebcast[0]).toBe('a');
  });
});

describe.concurrent('SET_WEBCASTS action', () => {
  test('sets webcastsById', () => {
    const webcasts = {
      'event1-0': createMockWebcast('event1-0'),
      'event2-0': createMockWebcast('event2-0'),
    };

    const state = gamedayReducer(initialState, {
      type: 'SET_WEBCASTS',
      webcasts,
    });
    expect(state.webcastsById).toEqual(webcasts);
  });

  test('removes invalid webcast ids from positionToWebcast', () => {
    const stateWithPositions: GamedayState = {
      ...initialState,
      positionToWebcast: [
        'event1-0',
        'invalid-id',
        'event2-0',
        null,
        null,
        null,
        null,
        null,
        null,
      ],
    };

    const webcasts = {
      'event1-0': createMockWebcast('event1-0'),
      'event2-0': createMockWebcast('event2-0'),
    };

    const state = gamedayReducer(stateWithPositions, {
      type: 'SET_WEBCASTS',
      webcasts,
    });
    expect(state.positionToWebcast[0]).toBe('event1-0');
    expect(state.positionToWebcast[1]).toBeNull(); // invalid-id was removed
    expect(state.positionToWebcast[2]).toBe('event2-0');
  });
});

describe.concurrent('ADD_WEBCAST_AT_POSITION action', () => {
  const stateWithLayout: GamedayState = {
    ...initialState,
    layoutId: 3, // Quad view (4 views)
  };

  test('adds webcast at specified position', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_WEBCAST_AT_POSITION',
      webcastId: 'event1-0',
      position: 2,
    });
    expect(state.positionToWebcast[2]).toBe('event1-0');
  });

  test('removes webcast from old position when moving', () => {
    const stateWithWebcast: GamedayState = {
      ...stateWithLayout,
      positionToWebcast: [
        'event1-0',
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
      ],
    };

    const state = gamedayReducer(stateWithWebcast, {
      type: 'ADD_WEBCAST_AT_POSITION',
      webcastId: 'event1-0',
      position: 2,
    });
    expect(state.positionToWebcast[0]).toBeNull();
    expect(state.positionToWebcast[2]).toBe('event1-0');
  });

  test('does nothing when layoutId is null', () => {
    const state = gamedayReducer(initialState, {
      type: 'ADD_WEBCAST_AT_POSITION',
      webcastId: 'event1-0',
      position: 0,
    });
    expect(state).toBe(initialState);
  });

  test('does nothing when position is out of bounds (negative)', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_WEBCAST_AT_POSITION',
      webcastId: 'event1-0',
      position: -1,
    });
    expect(state).toBe(stateWithLayout);
  });

  test('does nothing when position is out of bounds (beyond layout capacity)', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_WEBCAST_AT_POSITION',
      webcastId: 'event1-0',
      position: 5, // Quad view only has 4 positions (0-3)
    });
    expect(state).toBe(stateWithLayout);
  });
});

describe.concurrent('REMOVE_WEBCAST action', () => {
  test('removes webcast from positionToWebcast', () => {
    const stateWithWebcast: GamedayState = {
      ...initialState,
      positionToWebcast: [
        'event1-0',
        'event2-0',
        null,
        null,
        null,
        null,
        null,
        null,
        null,
      ],
    };

    const state = gamedayReducer(stateWithWebcast, {
      type: 'REMOVE_WEBCAST',
      webcastId: 'event1-0',
    });
    expect(state.positionToWebcast[0]).toBeNull();
    expect(state.positionToWebcast[1]).toBe('event2-0');
  });

  test('does nothing when webcast is not in any position', () => {
    const stateWithWebcast: GamedayState = {
      ...initialState,
      positionToWebcast: [
        'event1-0',
        null,
        null,
        null,
        null,
        null,
        null,
        null,
        null,
      ],
    };

    const state = gamedayReducer(stateWithWebcast, {
      type: 'REMOVE_WEBCAST',
      webcastId: 'nonexistent',
    });
    expect(state.positionToWebcast[0]).toBe('event1-0');
  });
});

describe.concurrent('SWAP_POSITIONS action', () => {
  test('swaps webcasts between two positions', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToWebcast: ['a', 'b', 'c', null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SWAP_POSITIONS',
      position1: 0,
      position2: 2,
    });
    expect(state.positionToWebcast[0]).toBe('c');
    expect(state.positionToWebcast[2]).toBe('a');
    expect(state.positionToWebcast[1]).toBe('b'); // unchanged
  });

  test('swaps with null position', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToWebcast: ['a', null, null, null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SWAP_POSITIONS',
      position1: 0,
      position2: 1,
    });
    expect(state.positionToWebcast[0]).toBeNull();
    expect(state.positionToWebcast[1]).toBe('a');
  });
});

describe.concurrent('RESET_WEBCASTS action', () => {
  test('clears all positions', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToWebcast: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
    };

    const state = gamedayReducer(stateWithWebcasts, { type: 'RESET_WEBCASTS' });
    expect(state.positionToWebcast.every((el) => el === null)).toBe(true);
  });

  test('preserves other state properties', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      layoutId: 3,
      chatSidebarVisible: false,
      positionToWebcast: ['a', 'b', null, null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, { type: 'RESET_WEBCASTS' });
    expect(state.layoutId).toBe(3);
    expect(state.chatSidebarVisible).toBe(false);
  });
});

describe.concurrent('TOGGLE_CHAT_SIDEBAR action', () => {
  test('toggles from visible to hidden', () => {
    const state = gamedayReducer(initialState, { type: 'TOGGLE_CHAT_SIDEBAR' });
    expect(state.chatSidebarVisible).toBe(false);
  });

  test('toggles from hidden to visible', () => {
    const stateWithHiddenChat: GamedayState = {
      ...initialState,
      chatSidebarVisible: false,
    };

    const state = gamedayReducer(stateWithHiddenChat, {
      type: 'TOGGLE_CHAT_SIDEBAR',
    });
    expect(state.chatSidebarVisible).toBe(true);
  });
});

describe.concurrent('SET_CURRENT_CHAT action', () => {
  test('sets current chat channel', () => {
    const state = gamedayReducer(initialState, {
      type: 'SET_CURRENT_CHAT',
      channel: 'new-channel',
    });
    expect(state.currentChat).toBe('new-channel');
  });
});

describe.concurrent('RESTORE_URL_STATE action', () => {
  test('restores layout and positions from URL state', () => {
    const urlState: GamedayUrlState = {
      layoutId: 3, // Quad view (4 views)
      positionToWebcast: ['a', 'b', 'c', 'd', null, null, null, null, null],
      chatSidebarVisible: true,
      currentChat: 'test-chat',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.layoutId).toBe(3);
    expect(state.positionToWebcast.slice(0, 4)).toEqual(['a', 'b', 'c', 'd']);
    expect(state.chatSidebarVisible).toBe(true);
    expect(state.currentChat).toBe('test-chat');
  });

  test('clears positions beyond layout capacity', () => {
    const urlState: GamedayUrlState = {
      layoutId: 0, // Single view (1 view)
      positionToWebcast: ['a', 'b', 'c', null, null, null, null, null, null],
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.positionToWebcast[0]).toBe('a');
    expect(state.positionToWebcast[1]).toBeNull();
    expect(state.positionToWebcast[2]).toBeNull();
  });

  test('restores chat visibility', () => {
    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToWebcast: createEmptyPositionArray(),
      chatSidebarVisible: false,
      currentChat: '',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.chatSidebarVisible).toBe(false);
  });

  test('preserves existing state when layoutId is null', () => {
    const existingState: GamedayState = {
      ...initialState,
      layoutId: 3,
      positionToWebcast: ['a', 'b', null, null, null, null, null, null, null],
    };

    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToWebcast: createEmptyPositionArray(),
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(existingState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.layoutId).toBe(3);
    expect(state.positionToWebcast[0]).toBe('a');
    expect(state.positionToWebcast[1]).toBe('b');
  });

  test('does not set currentChat when empty string in urlState', () => {
    const existingState: GamedayState = {
      ...initialState,
      currentChat: 'existing-chat',
    };

    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToWebcast: createEmptyPositionArray(),
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(existingState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.currentChat).toBe('existing-chat');
  });
});

describe.concurrent('default case', () => {
  test('returns unchanged state for unknown action', () => {
    const unknownAction = {
      type: 'UNKNOWN_ACTION',
    } as unknown as GamedayAction;
    const state = gamedayReducer(initialState, unknownAction);
    expect(state).toBe(initialState);
  });
});
