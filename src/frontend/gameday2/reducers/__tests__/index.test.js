const mockRef = { child: jest.fn() };
const mockDatabase = jest.fn(() => ({ ref: () => mockRef }));
const mockInitializeApp = jest.fn(() => ({ database: mockDatabase }));

jest.mock("firebase/compat/app", () => ({
  __esModule: true,
  default: { initializeApp: (...args) => mockInitializeApp(...args) },
}));
jest.mock("firebase/compat/database", () => ({}));
jest.mock("../../firebaseMirror", () =>
  jest.fn().mockImplementation(function MockFirebaseMirror({ ref }) {
    this.ref = ref;
    this.reducer =
      () =>
      (state = { data: {} }) =>
        state;
  })
);

const { default: gamedayReducer, firebaseMirror } = require("../index");

describe("gameday root reducer", () => {
  it("initializes the TBA GameDay Firebase app and wires the Firebase mirror to its root ref", () => {
    expect(mockInitializeApp).toHaveBeenCalledWith({
      apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
      authDomain: "tbatv-prod-hrd.firebaseapp.com",
      databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
    });
    expect(firebaseMirror.ref).toBe(mockRef);
  });

  it("combines all of the gameday reducers", () => {
    const state = gamedayReducer(undefined, { type: "@@INIT" });
    expect(Object.keys(state)).toEqual([
      "firebaseMirror",
      "webcastsById",
      "specialWebcastIds",
      "visibility",
      "videoGrid",
      "chats",
      "favoriteTeams",
    ]);
    expect(state.firebaseMirror).toEqual({ data: {} });
  });
});
