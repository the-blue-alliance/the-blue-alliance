"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, {
          enumerable: true,
          get: function () {
            return m[k];
          },
        });
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
  };
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const visibility_1 = __importDefault(require("../visibility"));
const types = __importStar(require("../../constants/ActionTypes"));
describe("visibility reducer", () => {
  const defaultState = {
    hashtagSidebar: false,
    chatSidebar: true,
    chatSidebarHasBeenVisible: true,
    tickerSidebar: false,
    layoutDrawer: false,
  };
  it("defaults all views to not visibile", () => {
    expect(visibility_1.default(undefined, {})).toEqual(defaultState);
  });
  it("toggles chat sidebar from true to false", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      chatSidebar: false,
      chatSidebarHasBeenVisible: true,
    });
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
  it("toggles chat sidebar from false to true", () => {
    const initialState = Object.assign({}, defaultState, {
      chatSidebar: false,
      chatSidebarHasBeenVisible: true,
    });
    const expectedState = Object.assign({}, defaultState, {
      chatSidebar: true,
      chatSidebarHasBeenVisible: true,
    });
    const action = {
      type: types.TOGGLE_CHAT_SIDEBAR_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
  it("toggles hashtag sidebar from false to true", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      hashtagSidebar: true,
    });
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
  it("toggles hashtag sidebar from true to false", () => {
    const initialState = Object.assign({}, defaultState, {
      hashtagSidebar: true,
    });
    const expectedState = defaultState;
    const action = {
      type: types.TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
  it("toggles layout drawer from false to true", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      layoutDrawer: true,
    });
    const action = {
      type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
  it("toggles layout drawer from true to false", () => {
    const initialState = Object.assign({}, defaultState, {
      layoutDrawer: true,
    });
    const expectedState = defaultState;
    const action = {
      type: types.TOGGLE_LAYOUT_DRAWER_VISIBILITY,
    };
    expect(visibility_1.default(initialState, action)).toEqual(expectedState);
  });
});
