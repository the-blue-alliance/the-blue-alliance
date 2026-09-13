import { describe, expect, test } from 'vitest';

import { MAX_VIEWS } from '~/lib/gameday/layouts';
import { createEmptyPositionArray } from '~/lib/gameday/reducer';
import {
  type GamedayUrlState,
  hasUrlStateToRestore,
  parseSearchParams,
  serializeToSearchParams,
} from '~/lib/gameday/useGamedayUrlSync';
import type { GamedaySearchParams } from '~/routes/gameday';

function createEmptyUrlState(): GamedayUrlState {
  return {
    layoutId: null,
    positionToContent: createEmptyPositionArray(),
    chatSidebarVisible: true,
    currentChat: '',
  };
}

describe('hasUrlStateToRestore', () => {
  test('returns false for empty state', () => {
    const state = createEmptyUrlState();
    expect(hasUrlStateToRestore(state)).toBe(false);
  });

  test('returns true when layoutId is set', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      layoutId: 3,
    };
    expect(hasUrlStateToRestore(state)).toBe(true);
  });

  test('returns true when any webcast position is set', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[2] = 'event1-0';

    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      positionToContent,
    };
    expect(hasUrlStateToRestore(state)).toBe(true);
  });

  test('returns true when currentChat is set', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      currentChat: 'customchat',
    };
    expect(hasUrlStateToRestore(state)).toBe(true);
  });

  test('returns true when chatSidebarVisible is false', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      chatSidebarVisible: false,
    };
    expect(hasUrlStateToRestore(state)).toBe(true);
  });

  test('returns true when multiple values are set', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[0] = 'event1-0';
    positionToContent[1] = 'event2-0';

    const state: GamedayUrlState = {
      layoutId: 3,
      positionToContent,
      chatSidebarVisible: false,
      currentChat: 'mychannel',
    };
    expect(hasUrlStateToRestore(state)).toBe(true);
  });
});

describe('parseSearchParams', () => {
  test('returns default state for empty params', () => {
    const params: GamedaySearchParams = {};
    const state = parseSearchParams(params);

    expect(state.layoutId).toBeNull();
    expect(state.positionToContent).toHaveLength(MAX_VIEWS);
    expect(state.positionToContent.every((p) => p === null)).toBe(true);
    expect(state.chatSidebarVisible).toBe(true);
    expect(state.currentChat).toBe('');
  });

  test('parses layout param', () => {
    const params: GamedaySearchParams = { layout: 3 };
    const state = parseSearchParams(params);

    expect(state.layoutId).toBe(3);
  });

  test('parses view params', () => {
    const params: GamedaySearchParams = {
      view_0: 'event1-0',
      view_2: 'event2-0',
      view_5: 'event3-1',
    };
    const state = parseSearchParams(params);

    expect(state.positionToContent[0]).toBe('event1-0');
    expect(state.positionToContent[1]).toBeNull();
    expect(state.positionToContent[2]).toBe('event2-0');
    expect(state.positionToContent[3]).toBeNull();
    expect(state.positionToContent[4]).toBeNull();
    expect(state.positionToContent[5]).toBe('event3-1');
  });

  test('parses a data panel from a view param', () => {
    const state = parseSearchParams({
      view_1: 'data-panel:match-recommendations',
    });

    expect(state.positionToContent[1]).toBe('data-panel:match-recommendations');
  });

  test('parses chat param as channel name', () => {
    const params: GamedaySearchParams = { chat: 'funroboticsnetwork' };
    const state = parseSearchParams(params);

    expect(state.chatSidebarVisible).toBe(true);
    expect(state.currentChat).toBe('funroboticsnetwork');
  });

  test('parses chat=hidden as hidden sidebar', () => {
    const params: GamedaySearchParams = { chat: 'hidden' };
    const state = parseSearchParams(params);

    expect(state.chatSidebarVisible).toBe(false);
    expect(state.currentChat).toBe('');
  });

  test('parses all params together', () => {
    const params: GamedaySearchParams = {
      layout: 4,
      view_0: 'event1-0',
      view_1: 'event2-0',
      view_3: 'event3-0',
      chat: 'mychannel',
    };
    const state = parseSearchParams(params);

    expect(state.layoutId).toBe(4);
    expect(state.positionToContent[0]).toBe('event1-0');
    expect(state.positionToContent[1]).toBe('event2-0');
    expect(state.positionToContent[2]).toBeNull();
    expect(state.positionToContent[3]).toBe('event3-0');
    expect(state.chatSidebarVisible).toBe(true);
    expect(state.currentChat).toBe('mychannel');
  });
});

describe('serializeToSearchParams', () => {
  test('returns empty object for default state', () => {
    const state = createEmptyUrlState();
    const params = serializeToSearchParams(state);

    expect(params).toEqual({});
  });

  test('serializes layoutId', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      layoutId: 5,
    };
    const params = serializeToSearchParams(state);

    expect(params.layout).toBe(5);
  });

  test('serializes webcast positions', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[0] = 'event1-0';
    positionToContent[2] = 'event2-0';

    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      positionToContent,
    };
    const params = serializeToSearchParams(state);

    expect(params.view_0).toBe('event1-0');
    expect(params.view_1).toBeUndefined();
    expect(params.view_2).toBe('event2-0');
  });

  test('serializes a data panel position', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[2] = 'data-panel:match-recommendations';

    const params = serializeToSearchParams({
      ...createEmptyUrlState(),
      positionToContent,
    });

    expect(params.view_2).toBe('data-panel:match-recommendations');
  });

  test('serializes chat channel', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      chatSidebarVisible: true,
      currentChat: 'mychannel',
    };
    const params = serializeToSearchParams(state);

    expect(params.chat).toBe('mychannel');
  });

  test('does not serialize empty chat channel when visible', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      chatSidebarVisible: true,
      currentChat: '',
    };
    const params = serializeToSearchParams(state);

    expect(params.chat).toBeUndefined();
  });

  test('serializes hidden chat as "hidden"', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      chatSidebarVisible: false,
      currentChat: 'mychannel',
    };
    const params = serializeToSearchParams(state);

    expect(params.chat).toBe('hidden');
  });

  test('serializes hidden chat with empty channel', () => {
    const state: GamedayUrlState = {
      ...createEmptyUrlState(),
      chatSidebarVisible: false,
      currentChat: '',
    };
    const params = serializeToSearchParams(state);

    expect(params.chat).toBe('hidden');
  });

  test('serializes all values together', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[0] = 'event1-0';
    positionToContent[1] = 'event2-0';
    positionToContent[3] = 'event3-0';

    const state: GamedayUrlState = {
      layoutId: 4,
      positionToContent,
      chatSidebarVisible: true,
      currentChat: 'mychannel',
    };
    const params = serializeToSearchParams(state);

    expect(params.layout).toBe(4);
    expect(params.view_0).toBe('event1-0');
    expect(params.view_1).toBe('event2-0');
    expect(params.view_2).toBeUndefined();
    expect(params.view_3).toBe('event3-0');
    expect(params.chat).toBe('mychannel');
  });
});

describe('round-trip serialization', () => {
  test('parse -> serialize preserves simple state', () => {
    const originalParams: GamedaySearchParams = {
      layout: 3,
      view_0: 'event1-0',
      chat: 'mychannel',
    };

    const state = parseSearchParams(originalParams);
    const serializedParams = serializeToSearchParams(state);

    expect(serializedParams.layout).toBe(originalParams.layout);
    expect(serializedParams.view_0).toBe(originalParams.view_0);
    expect(serializedParams.chat).toBe(originalParams.chat);
  });

  test('parse -> serialize preserves hidden chat', () => {
    const originalParams: GamedaySearchParams = {
      chat: 'hidden',
    };

    const state = parseSearchParams(originalParams);
    const serializedParams = serializeToSearchParams(state);

    expect(serializedParams.chat).toBe('hidden');
  });

  test('parse -> serialize preserves complex state', () => {
    const originalParams: GamedaySearchParams = {
      layout: 8,
      view_0: 'event1-0',
      view_1: 'event2-0',
      view_2: 'event3-0',
      view_4: 'event4-0',
      view_7: 'event5-0',
      chat: 'customchannel',
    };

    const state = parseSearchParams(originalParams);
    const serializedParams = serializeToSearchParams(state);

    expect(serializedParams.layout).toBe(8);
    expect(serializedParams.view_0).toBe('event1-0');
    expect(serializedParams.view_1).toBe('event2-0');
    expect(serializedParams.view_2).toBe('event3-0');
    expect(serializedParams.view_3).toBeUndefined();
    expect(serializedParams.view_4).toBe('event4-0');
    expect(serializedParams.view_5).toBeUndefined();
    expect(serializedParams.view_6).toBeUndefined();
    expect(serializedParams.view_7).toBe('event5-0');
    expect(serializedParams.chat).toBe('customchannel');
  });

  test('serialize -> parse preserves state', () => {
    const positionToContent = createEmptyPositionArray();
    positionToContent[0] = 'event1-0';
    positionToContent[3] = 'event2-0';

    const originalState: GamedayUrlState = {
      layoutId: 5,
      positionToContent,
      chatSidebarVisible: true,
      currentChat: 'testchannel',
    };

    const params = serializeToSearchParams(originalState);
    const parsedState = parseSearchParams(params);

    expect(parsedState.layoutId).toBe(originalState.layoutId);
    expect(parsedState.positionToContent[0]).toBe(
      originalState.positionToContent[0],
    );
    expect(parsedState.positionToContent[3]).toBe(
      originalState.positionToContent[3],
    );
    expect(parsedState.chatSidebarVisible).toBe(
      originalState.chatSidebarVisible,
    );
    expect(parsedState.currentChat).toBe(originalState.currentChat);
  });
});
