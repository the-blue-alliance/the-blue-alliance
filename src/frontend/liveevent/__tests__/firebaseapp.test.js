/* @jest-environment jsdom */

const mockInitializeApp = jest.fn(() => "app");
const mockUseEmulator = jest.fn();

jest.mock("firebase/compat/app", () => ({
  __esModule: true,
  default: {
    initializeApp: (...args) => mockInitializeApp(...args),
    database: () => ({ useEmulator: (...args) => mockUseEmulator(...args) }),
  },
}));
jest.mock("firebase/compat/database", () => ({}));

const configKeys = [
  "firebaseDatabaseEmulatorHost",
  "firebaseProjectId",
  "firebaseDatabaseURL",
  "firebaseApiKey",
  "firebaseAuthDomain",
  "firebaseStorageBucket",
  "firebaseMessagingSenderId",
  "firebaseAppId",
];

const loadApp = () => {
  let app;
  jest.isolateModules(() => {
    app = require("../firebaseapp").default;
  });
  return app;
};

describe("liveevent FirebaseApp", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    configKeys.forEach((key) => delete window[key]);
  });

  it("uses defaults when no config is on the window", () => {
    expect(loadApp()).toBe("app");
    expect(mockInitializeApp).toHaveBeenCalledWith({
      apiKey: "",
      authDomain: "",
      databaseURL: "",
      projectId: "demo-test",
      storageBucket: "",
      messagingSenderId: "",
      appId: "",
    });
    expect(mockUseEmulator).not.toHaveBeenCalled();
  });

  it("uses the config from the window", () => {
    Object.assign(window, {
      firebaseProjectId: "tba",
      firebaseDatabaseURL: "https://tba.firebaseio.com",
      firebaseApiKey: "key",
      firebaseAuthDomain: "tba.firebaseapp.com",
      firebaseStorageBucket: "bucket",
      firebaseMessagingSenderId: "sender",
      firebaseAppId: "appid",
    });
    loadApp();
    expect(mockInitializeApp).toHaveBeenCalledWith({
      apiKey: "key",
      authDomain: "tba.firebaseapp.com",
      databaseURL: "https://tba.firebaseio.com",
      projectId: "tba",
      storageBucket: "bucket",
      messagingSenderId: "sender",
      appId: "appid",
    });
  });

  it("builds an emulator database URL and connects to the emulator", () => {
    window.firebaseDatabaseEmulatorHost = "localhost:9000";
    loadApp();
    expect(mockInitializeApp.mock.calls[0][0].databaseURL).toBe(
      "http://localhost:9000?ns=demo-test"
    );
    expect(mockUseEmulator).toHaveBeenCalledWith("localhost", 9000);
  });

  it("keeps an explicit database URL when using the emulator", () => {
    window.firebaseDatabaseEmulatorHost = "localhost:9000";
    window.firebaseDatabaseURL = "http://localhost:9000?ns=custom";
    loadApp();
    expect(mockInitializeApp.mock.calls[0][0].databaseURL).toBe(
      "http://localhost:9000?ns=custom"
    );
  });
});
