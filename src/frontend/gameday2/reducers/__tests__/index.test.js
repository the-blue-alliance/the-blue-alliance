const mockRef = { child: jest.fn() };
const mockDatabase = jest.fn(() => ({ ref: () => mockRef }));
const mockInitializeApp = jest.fn(() => ({ database: mockDatabase }));

jest.mock("firebase/compat/app", () => ({
  __esModule: true,
  default: { initializeApp: (...args) => mockInitializeApp(...args) },
}));
jest.mock("firebase/compat/database", () => ({}));
jest.mock("firedux", () =>
  jest.fn().mockImplementation(function MockFiredux({ ref }) {
    this.ref = ref;
    this.reducer =
      () =>
      (state = { data: {} }) =>
        state;
  })
);

const { default: gamedayReducer, firedux } = require("../index");

describe("gameday root reducer", () => {
  it("initializes the TBA GameDay Firebase app and wires firedux to its root ref", () => {
    expect(mockInitializeApp).toHaveBeenCalledWith({
      apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
      authDomain: "tbatv-prod-hrd.firebaseapp.com",
      databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
    });
    expect(firedux.ref).toBe(mockRef);
  });

  it("combines all of the gameday reducers", () => {
    const state = gamedayReducer(undefined, { type: "@@INIT" });
    expect(Object.keys(state)).toEqual([
      "firedux",
      "webcastsById",
      "specialWebcastIds",
      "visibility",
      "videoGrid",
      "chats",
      "favoriteTeams",
    ]);
    expect(state.firedux).toEqual({ data: {} });
  });
});
