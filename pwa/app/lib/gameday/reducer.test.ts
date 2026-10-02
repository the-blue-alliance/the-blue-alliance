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

describe('createEmptyPositionArray', () => {
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

describe('initialState', () => {
  test('has expected default values', () => {
    expect(initialState.layoutId).toBeNull();
    expect(initialState.positionToContent).toHaveLength(MAX_VIEWS);
    expect(initialState.chatSidebarVisible).toBe(true);
    expect(initialState.currentChat).toBe('funroboticsnetwork');
    expect(initialState.webcastsById).toEqual({});
    expect(initialState.hasRestoredUrlState).toBe(false);
  });
});

describe('SET_LAYOUT action', () => {
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
      positionToContent: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
    };

    // Switch to quad view (4 views)
    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SET_LAYOUT',
      layoutId: 3,
    });
    expect(state.positionToContent.slice(0, 4)).toEqual(['a', 'b', 'c', 'd']);
  });

  test('pads with nulls when switching to larger layout', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      layoutId: 0, // 1 view
      positionToContent: ['a', null, null, null, null, null, null, null, null],
    };

    // Switch to quad view (4 views)
    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SET_LAYOUT',
      layoutId: 3,
    });
    expect(state.positionToContent).toHaveLength(MAX_VIEWS);
    expect(state.positionToContent[0]).toBe('a');
  });
});

describe('SET_WEBCASTS action', () => {
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

  test('removes invalid webcast ids from positionToContent', () => {
    const stateWithPositions: GamedayState = {
      ...initialState,
      positionToContent: [
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
    expect(state.positionToContent[0]).toBe('event1-0');
    expect(state.positionToContent[1]).toBeNull(); // invalid-id was removed
    expect(state.positionToContent[2]).toBe('event2-0');
  });

  test('preserves registered data panels when webcasts update', () => {
    const stateWithPanel: GamedayState = {
      ...initialState,
      positionToContent: [
        'data-panel:match-recommendations',
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

    const state = gamedayReducer(stateWithPanel, {
      type: 'SET_WEBCASTS',
      webcasts: {},
      dataPanelIds: ['data-panel:match-recommendations'],
    });

    expect(state.positionToContent[0]).toBe('data-panel:match-recommendations');
  });
});

describe('ADD_CONTENT_AT_POSITION action', () => {
  const stateWithLayout: GamedayState = {
    ...initialState,
    layoutId: 3, // Quad view (4 views)
  };

  test('adds webcast at specified position', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'event1-0',
      position: 2,
    });
    expect(state.positionToContent[2]).toBe('event1-0');
  });

  test('removes webcast from old position when moving', () => {
    const stateWithWebcast: GamedayState = {
      ...stateWithLayout,
      positionToContent: [
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
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'event1-0',
      position: 2,
    });
    expect(state.positionToContent[0]).toBeNull();
    expect(state.positionToContent[2]).toBe('event1-0');
  });

  test('keeps only one instance of a data panel', () => {
    const stateWithPanel: GamedayState = {
      ...stateWithLayout,
      positionToContent: [
        'data-panel:match-recommendations',
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

    const state = gamedayReducer(stateWithPanel, {
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'data-panel:match-recommendations',
      position: 2,
    });

    expect(state.positionToContent.slice(0, 3)).toEqual([
      null,
      null,
      'data-panel:match-recommendations',
    ]);
  });

  test('does nothing when layoutId is null', () => {
    const state = gamedayReducer(initialState, {
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'event1-0',
      position: 0,
    });
    expect(state).toBe(initialState);
  });

  test('does nothing when position is out of bounds (negative)', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'event1-0',
      position: -1,
    });
    expect(state).toBe(stateWithLayout);
  });

  test('does nothing when position is out of bounds (beyond layout capacity)', () => {
    const state = gamedayReducer(stateWithLayout, {
      type: 'ADD_CONTENT_AT_POSITION',
      contentId: 'event1-0',
      position: 5, // Quad view only has 4 positions (0-3)
    });
    expect(state).toBe(stateWithLayout);
  });
});

describe('REMOVE_CONTENT action', () => {
  test('removes webcast from positionToContent', () => {
    const stateWithWebcast: GamedayState = {
      ...initialState,
      positionToContent: [
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
      type: 'REMOVE_CONTENT',
      contentId: 'event1-0',
    });
    expect(state.positionToContent[0]).toBeNull();
    expect(state.positionToContent[1]).toBe('event2-0');
  });

  test('does nothing when webcast is not in any position', () => {
    const stateWithWebcast: GamedayState = {
      ...initialState,
      positionToContent: [
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
      type: 'REMOVE_CONTENT',
      contentId: 'nonexistent',
    });
    expect(state.positionToContent[0]).toBe('event1-0');
  });
});

describe('SWAP_POSITIONS action', () => {
  test('swaps webcasts between two positions', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToContent: ['a', 'b', 'c', null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SWAP_POSITIONS',
      position1: 0,
      position2: 2,
    });
    expect(state.positionToContent[0]).toBe('c');
    expect(state.positionToContent[2]).toBe('a');
    expect(state.positionToContent[1]).toBe('b'); // unchanged
  });

  test('swaps with null position', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToContent: ['a', null, null, null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, {
      type: 'SWAP_POSITIONS',
      position1: 0,
      position2: 1,
    });
    expect(state.positionToContent[0]).toBeNull();
    expect(state.positionToContent[1]).toBe('a');
  });
});

describe('RESET_CONTENT action', () => {
  test('clears all positions', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      positionToContent: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'],
    };

    const state = gamedayReducer(stateWithWebcasts, { type: 'RESET_CONTENT' });
    expect(state.positionToContent.every((el) => el === null)).toBe(true);
  });

  test('preserves other state properties', () => {
    const stateWithWebcasts: GamedayState = {
      ...initialState,
      layoutId: 3,
      chatSidebarVisible: false,
      positionToContent: ['a', 'b', null, null, null, null, null, null, null],
    };

    const state = gamedayReducer(stateWithWebcasts, { type: 'RESET_CONTENT' });
    expect(state.layoutId).toBe(3);
    expect(state.chatSidebarVisible).toBe(false);
  });
});

describe('TOGGLE_CHAT_SIDEBAR action', () => {
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

describe('SET_CURRENT_CHAT action', () => {
  test('sets current chat channel', () => {
    const state = gamedayReducer(initialState, {
      type: 'SET_CURRENT_CHAT',
      channel: 'new-channel',
    });
    expect(state.currentChat).toBe('new-channel');
  });
});

describe('RESTORE_URL_STATE action', () => {
  test('restores layout and positions from URL state', () => {
    const urlState: GamedayUrlState = {
      layoutId: 3, // Quad view (4 views)
      positionToContent: ['a', 'b', 'c', 'd', null, null, null, null, null],
      chatSidebarVisible: true,
      currentChat: 'test-chat',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.layoutId).toBe(3);
    expect(state.positionToContent.slice(0, 4)).toEqual(['a', 'b', 'c', 'd']);
    expect(state.chatSidebarVisible).toBe(true);
    expect(state.currentChat).toBe('test-chat');
  });

  test('clears positions beyond layout capacity', () => {
    const urlState: GamedayUrlState = {
      layoutId: 0, // Single view (1 view)
      positionToContent: ['a', 'b', 'c', null, null, null, null, null, null],
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.positionToContent[0]).toBe('a');
    expect(state.positionToContent[1]).toBeNull();
    expect(state.positionToContent[2]).toBeNull();
  });

  test('restores chat visibility', () => {
    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToContent: createEmptyPositionArray(),
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
      positionToContent: ['a', 'b', null, null, null, null, null, null, null],
    };

    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToContent: createEmptyPositionArray(),
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(existingState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.layoutId).toBe(3);
    expect(state.positionToContent[0]).toBe('a');
    expect(state.positionToContent[1]).toBe('b');
  });

  test('does not set currentChat when empty string in urlState', () => {
    const existingState: GamedayState = {
      ...initialState,
      currentChat: 'existing-chat',
    };

    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToContent: createEmptyPositionArray(),
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(existingState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.currentChat).toBe('existing-chat');
  });

  test('marks URL state as restored', () => {
    const urlState: GamedayUrlState = {
      layoutId: null,
      positionToContent: createEmptyPositionArray(),
      chatSidebarVisible: true,
      currentChat: '',
    };

    const state = gamedayReducer(initialState, {
      type: 'RESTORE_URL_STATE',
      urlState,
    });
    expect(state.hasRestoredUrlState).toBe(true);
  });
});

describe('LOAD_EVENT_WEBCASTS', () => {
  test('sets layout and populates positions with event webcasts', () => {
    const webcasts = [
      createMockWebcast('2026tuis-0'),
      createMockWebcast('2026tuis-1'),
    ];
    const state = gamedayReducer(initialState, {
      type: 'LOAD_EVENT_WEBCASTS',
      webcasts,
      layoutId: 1, // Vertical Split (2 views)
    });
    expect(state.layoutId).toBe(1);
    expect(state.positionToContent[0]).toBe('2026tuis-0');
    expect(state.positionToContent[1]).toBe('2026tuis-1');
    expect(state.positionToContent[2]).toBeNull();
  });

  test('caps webcasts at layout capacity', () => {
    const webcasts = [
      createMockWebcast('2026tuis-0'),
      createMockWebcast('2026tuis-1'),
      createMockWebcast('2026tuis-2'),
    ];
    // Layout 0 = Single View (1 view)
    const state = gamedayReducer(initialState, {
      type: 'LOAD_EVENT_WEBCASTS',
      webcasts,
      layoutId: 0,
    });
    expect(state.layoutId).toBe(0);
    expect(state.positionToContent[0]).toBe('2026tuis-0');
    expect(state.positionToContent[1]).toBeNull();
  });

  test('fills remaining positions with null', () => {
    const webcasts = [createMockWebcast('2026tuis-0')];
    const state = gamedayReducer(initialState, {
      type: 'LOAD_EVENT_WEBCASTS',
      webcasts,
      layoutId: 0,
    });
    expect(state.positionToContent).toHaveLength(MAX_VIEWS);
    expect(state.positionToContent.filter((p) => p !== null)).toHaveLength(1);
  });
});

describe('default case', () => {
  test('returns unchanged state for unknown action', () => {
    const unknownAction = {
      type: 'UNKNOWN_ACTION',
    } as unknown as GamedayAction;
    const state = gamedayReducer(initialState, unknownAction);
    expect(state).toBe(initialState);
  });
});
