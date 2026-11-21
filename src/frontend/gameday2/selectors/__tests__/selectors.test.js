import * as selectors from "../../selectors";

describe("getWebcastIds selector", () => {
  const sampleState = {
    webcastsById: {
      a: {},
      b: {},
      c: {},
    },
  };

  it("correctly extracts the ids", () => {
    expect(selectors.getWebcastIds(sampleState)).toEqual(["a", "b", "c"]);
  });
});

describe("getWebcastIdsInDisplayOrder selector", () => {
  const sampleState = {
    webcastsById: {
      a: {
        id: "a",
        sortOrder: 3,
      },
      b: {
        id: "b",
        sortOrder: 1,
      },
      c: {
        id: "c",
        sortOrder: 2,
      },
      d: {
        id: "d",
        name: "ccc",
      },
      e: {
        id: "e",
        name: "aaa",
      },
    },
  };

  it("correctly sorts and returns the ids", () => {
    expect(selectors.getWebcastIdsInDisplayOrder(sampleState)).toEqual([
      "b",
      "c",
      "a",
      "e",
      "d",
    ]);
  });
});

describe("getChats selector", () => {
  it("correctly extracts the chats portion of the state", () => {
    const sampleState = {
      chats: {
        chats: {
          chat: {
            name: "chat",
            channel: "test",
          },
        },
      },
      other: {},
    };

    expect(selectors.getChats(sampleState)).toEqual({
      chats: {
        chat: {
          name: "chat",
          channel: "test",
        },
      },
    });
  });
});

describe("getChatsInDisplayOrder selector", () => {
  it("correctly extrats and sorts the chats", () => {
    const sampleState = {
      chats: {
        chats: {
          chat1: {
            name: "Second in order",
            channel: "chat1",
          },
          chat2: {
            name: "First in order",
            channel: "chat2",
          },
        },
      },
    };

    expect(selectors.getChatsInDisplayOrder(sampleState)).toEqual([
      {
        name: "First in order",
        channel: "chat2",
      },
      {
        name: "Second in order",
        channel: "chat1",
      },
    ]);
  });
});

describe("firedux-backed selectors", () => {
  const props = { webcast: { key: "2024casj" } };

  it("returns no matches when there is no firedux data for the event", () => {
    expect(
      selectors.getEventMatches({ firedux: { data: null } }, props)
    ).toEqual([]);
    expect(
      selectors.getEventMatches({ firedux: { data: { e: {} } } }, props)
    ).toEqual([]);
    expect(
      selectors.getEventMatches(
        { firedux: { data: { e: { "2024casj": {} } } } },
        props
      )
    ).toEqual([]);
  });

  const state = {
    firedux: {
      data: {
        e: {
          "2024casj": {
            m: {
              f1m1: { c: "f", s: 1, m: 1, r: -1, b: -1 },
              qm2: { c: "qm", s: 1, m: 2, r: 10, b: 20 },
              sf1m1: { c: "sf", s: 1, m: 1, r: -1, b: -1 },
              qm1: { c: "qm", s: 1, m: 1, r: 30, b: 40 },
              odd: { c: "xx", s: 1, m: 1, r: -1, b: -1 },
            },
          },
        },
        le: { "2024casj": { mk: "qm3" } },
      },
    },
  };

  it("sorts event matches by play order, putting unknown ones first", () => {
    const matches = selectors.getEventMatches(state, props);
    expect(matches.map((m) => m.shortKey)).toEqual([
      "odd",
      "qm1",
      "qm2",
      "sf1m1",
      "f1m1",
    ]);
    expect(matches[1].key).toBe("2024casj_qm1");
  });

  it("returns the last played match followed by unplayed matches after it", () => {
    const ticker = selectors.getTickerMatches(state, props);
    expect(ticker.map((m) => m.shortKey)).toEqual(["qm2", "sf1m1", "f1m1"]);
  });

  it("returns only unplayed matches when nothing has been played", () => {
    const unplayed = {
      firedux: {
        data: {
          e: {
            "2024casj": { m: { qm1: { c: "qm", s: 1, m: 1, r: -1, b: -1 } } },
          },
        },
      },
    };
    expect(
      selectors.getTickerMatches(unplayed, props).map((m) => m.shortKey)
    ).toEqual(["qm1"]);
  });

  it("returns the current match state for the event, or null", () => {
    expect(selectors.getCurrentMatchState(state, props)).toEqual({ mk: "qm3" });
    expect(
      selectors.getCurrentMatchState({ firedux: { data: {} } }, props)
    ).toBeNull();
    expect(
      selectors.getCurrentMatchState({ firedux: { data: null } }, props)
    ).toBeNull();
  });
});
