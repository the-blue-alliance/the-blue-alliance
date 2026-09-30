/* @jest-environment jsdom */

const mockListeners = {};
const mockOff = jest.fn();
const mockRef = {
  child: jest.fn((path) => ({
    on: (event, cb) => {
      mockListeners[path] = cb;
    },
    off: (event) => mockOff(path, event),
  })),
};
const mockRender = jest.fn();
const mockGAInitialize = jest.fn();

jest.mock("../gameday2.less", () => ({}));
jest.mock("react-ga4", () => ({
  __esModule: true,
  default: { initialize: (...args) => mockGAInitialize(...args) },
}));
jest.mock("react-dom/client", () => ({
  createRoot: () => ({ render: (...args) => mockRender(...args) }),
}));
jest.mock("../components/GamedayFrame", () => () => null);
jest.mock("firebase/compat/app", () => ({
  __esModule: true,
  default: {
    initializeApp: () => ({ database: () => ({ ref: () => mockRef }) }),
  },
}));
jest.mock("firebase/compat/database", () => ({}));
// query-string ships as ESM only, which this Jest setup does not transform, so
// stand in a minimal equivalent built on URLSearchParams (sorted keys, like
// query-string's default stringify).
jest.mock("query-string", () => ({
  __esModule: true,
  default: {
    parse: (str) =>
      Object.fromEntries(new URLSearchParams(str.replace(/^[#?]/, ""))),
    stringify: (obj) =>
      new URLSearchParams(
        Object.keys(obj)
          .sort()
          .map((key) => [key, String(obj[key])])
      ).toString(),
  },
}));
jest.mock("firedux", () =>
  jest.fn().mockImplementation(function MockFiredux({ ref }) {
    this.ref = ref;
    this.watching = {};
    this.watch = jest.fn((path) => {
      this.watching[path] = true;
    });
    this.reducer =
      () =>
      (state = { data: {} }) =>
        state;
  })
);

const specialWebcast = {
  key_name: "bluezone",
  name: "BlueZone",
  type: "twitch",
  channel: "bluezone",
};

const liveEvents = {
  "2024casj": {
    key: "2024casj",
    name: "Silicon Valley Regional",
    short_name: "SVR",
    webcasts: [
      { type: "twitch", channel: "svr" },
      { type: "twitch", channel: "svr2" },
    ],
  },
  "2024nyny": {
    key: "2024nyny",
    name: "New York City Regional",
    webcasts: [{ type: "twitch", channel: "nyc" }],
  },
  "2024noweb": { key: "2024noweb", name: "No Webcast Regional" },
};

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0));

const setUpPage = ({ hash, defaultChat }) => {
  document.body.innerHTML = `
    <script id="webcasts_json" type="application/json">${JSON.stringify({
      special_webcasts: [specialWebcast],
      ongoing_events_w_webcasts: [],
    })}</script>
    <div id="default_chat">${defaultChat}</div>
    <div id="content"></div>`;
  window.history.replaceState(null, "", `/gameday${hash}`);
};

// Captures the store via the Redux DevTools compose hook that gameday2.js
// honors when present.
let mockStore;
const loadGameday = ({ devtools = true } = {}) => {
  let firedux;
  jest.isolateModules(() => {
    const { compose } = require("redux");
    window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ =
      devtools &&
      ((...enhancers) =>
        (createStore) =>
        (...args) => {
          mockStore = compose(...enhancers)(createStore)(...args);
          return mockStore;
        });
    require("../gameday2");
    firedux = require("../reducers").firedux;
  });
  return firedux;
};

const hashParams = () =>
  Object.fromEntries(new URLSearchParams(window.location.hash.slice(1)));

describe("gameday2 entry point", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.keys(mockListeners).forEach((key) => delete mockListeners[key]);
    global.fetch = jest.fn(() =>
      Promise.resolve({
        status: 200,
        json: () => Promise.resolve([{ model_key: "frc254" }]),
      })
    );
  });

  it("renders the app, restores state from the URL hash, and keeps Firebase subscriptions in sync", async () => {
    setUpPage({
      hash: "#layout=3&view_0=2024casj-0&view_1=2024casj-1&view_2=2024nyny-0&view_3=missing-0&livescore_0=true&livescore_2=true&chat=nyc",
      defaultChat: "svr",
    });
    const firedux = loadGameday();
    const store = mockStore;
    expect(firedux.dispatch).toBe(store.dispatch);

    expect(mockGAInitialize).toHaveBeenCalledWith("UA-1090782-9");
    expect(mockRender).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith("/_/account/favorites/1", {
      credentials: "same-origin",
    });
    expect(mockRef.child).toHaveBeenCalledWith("special_webcasts");
    expect(mockRef.child).toHaveBeenCalledWith("live_events");

    // Special webcasts update from Firebase
    mockListeners.special_webcasts({ val: () => [specialWebcast] });

    // First live events update restores the webcasts, livescores and chat
    mockListeners.live_events({ val: () => liveEvents });
    expect(store.getState().chats.defaultChat).toBe("svr");
    expect(store.getState().chats.currentChat).toBe("nyc");
    expect(firedux.watch).toHaveBeenCalledWith("e/2024casj/m");
    expect(firedux.watch).toHaveBeenCalledWith("e/2024nyny/m");
    expect(firedux.watch).toHaveBeenCalledWith("le/2024casj");
    expect(firedux.watch).toHaveBeenCalledWith("le/2024nyny");
    expect(
      firedux.watch.mock.calls.filter(([path]) => path === "e/2024casj/m")
    ).toHaveLength(1);

    expect(hashParams()).toEqual({
      layout: "3",
      view_0: "2024casj-0",
      view_1: "2024casj-1",
      view_2: "2024nyny-0",
      livescore_0: "true",
      livescore_2: "true",
      chat: "nyc",
    });

    // Removing one of two webcasts for an event keeps the event subscription
    const { removeWebcast, togglePositionLivescore } = require("../actions");
    store.dispatch(removeWebcast("2024casj-1"));
    expect(mockOff).not.toHaveBeenCalledWith("e/2024casj/m", "value");

    // Removing the last webcast for an event unsubscribes from it
    store.dispatch(removeWebcast("2024nyny-0"));
    expect(mockOff).toHaveBeenCalledWith("e/2024nyny/m", "value");
    expect(mockOff).toHaveBeenCalledWith("le/2024nyny", "value");
    expect(firedux.watching["e/2024nyny/m"]).toBe(false);
    expect(firedux.watching["le/2024nyny"]).toBe(false);

    // Turning off a livescore unsubscribes from it
    store.dispatch(togglePositionLivescore(0));
    expect(mockOff).toHaveBeenCalledWith("le/2024casj", "value");
    expect(hashParams().livescore_0).toBeUndefined();

    // Later live event updates don't re-run the hash restoration, and a null
    // snapshot leaves the webcasts alone
    firedux.watch.mockClear();
    mockListeners.live_events({ val: () => null });
    mockListeners.live_events({ val: () => liveEvents });
    expect(firedux.watch).not.toHaveBeenCalled();

    await flushPromises();
    expect(mockStore.getState().favoriteTeams).toEqual(new Set(["frc254"]));
    // Pins current (buggy) behavior: the later live_events update resets the
    // default chat that was restored from the page on first load.
    expect(mockStore.getState().chats.defaultChat).toBe("firstupdatesnow");
  });

  it("hides the chat sidebar when requested and ignores invalid layouts", async () => {
    setUpPage({ hash: "#layout=abc&chat=hidden", defaultChat: "" });
    global.fetch = jest.fn(() => Promise.resolve({ status: 401 }));
    loadGameday();
    mockListeners.live_events({ val: () => liveEvents });
    expect(hashParams()).toEqual({ chat: "hidden" });
    expect(mockStore.getState().videoGrid.layoutSet).toBe(false);
    expect(mockStore.getState().visibility.chatSidebar).toBe(false);
    await flushPromises();
    expect(mockStore.getState().favoriteTeams).toEqual(new Set());
  });

  it("uses the default chat when no chat is given in the URL", () => {
    setUpPage({ hash: "", defaultChat: "svr" });
    loadGameday({ devtools: false });
    mockListeners.live_events({ val: () => liveEvents });
    expect(hashParams()).toEqual({ chat: "svr" });
  });
});
