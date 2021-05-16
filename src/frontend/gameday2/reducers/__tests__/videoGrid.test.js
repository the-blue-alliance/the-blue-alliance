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
const videoGrid_1 = __importDefault(require("../videoGrid"));
const LayoutConstants_1 = require("../../constants/LayoutConstants");
const types = __importStar(require("../../constants/ActionTypes"));
describe("video grid recuder", () => {
  const defaultPositionMap = new Array(LayoutConstants_1.MAX_SUPPORTED_VIEWS);
  const defaultDomOrder = new Array(LayoutConstants_1.MAX_SUPPORTED_VIEWS);
  const defaultDomOrderLivescoreOn = new Array(
    LayoutConstants_1.MAX_SUPPORTED_VIEWS
  );
  defaultDomOrder.fill(null);
  defaultPositionMap.fill(-1);
  defaultDomOrderLivescoreOn.fill(null);
  const getDefaultPositionMap = () => defaultPositionMap.slice(0);
  const getDefaultDomOrder = () => defaultDomOrder.slice(0);
  const getDefaultDomOrderLivescoreOn = () =>
    defaultDomOrderLivescoreOn.slice(0);
  const defaultState = {
    layoutId: 0,
    layoutSet: false,
    displayed: [],
    domOrder: defaultDomOrder,
    positionMap: defaultPositionMap,
    domOrderLivescoreOn: defaultDomOrderLivescoreOn,
  };
  it("defaults to the default state", () => {
    expect(videoGrid_1.default(undefined, {})).toEqual(defaultState);
  });
  it("sets the layout", () => {
    const initialState = defaultState;
    const expectedState = Object.assign({}, defaultState, {
      layoutId: 5,
      layoutSet: true,
    });
    const action = {
      type: types.SET_LAYOUT,
      layoutId: 5,
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  it("adds a webcast at the 0th position", () => {
    const initialState = Object.assign({}, defaultState, {
      layoutId: 0,
      layoutSet: true,
    });
    const domOrder = getDefaultDomOrder();
    domOrder[0] = "webcast1";
    const positionMap = getDefaultPositionMap();
    positionMap[0] = 0;
    const domOrderLivescoreOn = getDefaultDomOrderLivescoreOn();
    domOrderLivescoreOn[0] = false;
    const expectedState = Object.assign({}, initialState, {
      displayed: ["webcast1"],
      domOrder,
      positionMap,
      domOrderLivescoreOn,
    });
    const action = {
      type: types.ADD_WEBCAST_AT_POSITION,
      webcastId: "webcast1",
      position: 0,
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  it("adds a webcast in the next available DOM position", () => {
    const domOrder = getDefaultDomOrder();
    domOrder[1] = "webcast1";
    const positionMap = getDefaultPositionMap();
    positionMap[0] = 1;
    const domOrderLivescoreOn = getDefaultDomOrderLivescoreOn();
    domOrderLivescoreOn[0] = false;
    domOrderLivescoreOn[1] = false;
    const initialState = Object.assign({}, defaultState, {
      layoutId: 1,
      layoutSet: true,
      displayed: ["webcast1"],
      domOrder,
      positionMap,
      domOrderLivescoreOn,
    });
    const expectedDomOrder = domOrder.slice(0);
    expectedDomOrder[0] = "webcast2";
    const expectedPositionMap = positionMap.slice(0);
    expectedPositionMap[1] = 0;
    const expectedState = Object.assign({}, initialState, {
      displayed: ["webcast1", "webcast2"],
      domOrder: expectedDomOrder,
      positionMap: expectedPositionMap,
    });
    const action = {
      type: types.ADD_WEBCAST_AT_POSITION,
      webcastId: "webcast2",
      position: 1,
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  it("maintains as many webcasts as possible when switching to a layout with fewer views", () => {
    const domOrder = getDefaultDomOrder();
    domOrder[0] = "webcast1";
    domOrder[1] = "webcast2";
    domOrder[2] = "webcast3";
    const positionMap = getDefaultPositionMap();
    positionMap[0] = 0;
    positionMap[1] = 1;
    positionMap[2] = 2;
    const initialState = Object.assign({}, defaultState, {
      layoutId: 2,
      layoutSet: true,
      displayed: ["webcast1", "webcast2", "webcast3"],
      domOrder,
      positionMap,
    });
    const expectedDomOrder = domOrder.slice(0);
    expectedDomOrder[2] = null;
    const expectedPositionMap = positionMap.slice(0);
    expectedPositionMap[2] = -1;
    const expectedState = Object.assign({}, initialState, {
      layoutId: 1,
      displayed: ["webcast1", "webcast2"],
      domOrder: expectedDomOrder,
      positionMap: expectedPositionMap,
    });
    const action = {
      type: types.SET_LAYOUT,
      layoutId: 1,
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  it("removes a webcast", () => {
    const domOrder = getDefaultDomOrder();
    domOrder[0] = "webcast1";
    domOrder[1] = "webcast2";
    domOrder[2] = "webcast3";
    const positionMap = getDefaultPositionMap();
    positionMap[0] = 0;
    positionMap[1] = 1;
    positionMap[2] = 2;
    const initialState = Object.assign({}, defaultState, {
      layoutId: 2,
      layoutSet: true,
      displayed: ["webcast1", "webcast2", "webcast3"],
      domOrder,
      positionMap,
    });
    const expectedDomOrder = domOrder.slice(0);
    expectedDomOrder[1] = null;
    const expectedPositionMap = positionMap.slice(0);
    expectedPositionMap[1] = -1;
    const expectedState = Object.assign({}, initialState, {
      displayed: ["webcast1", "webcast3"],
      domOrder: expectedDomOrder,
      positionMap: expectedPositionMap,
    });
    const action = {
      type: types.REMOVE_WEBCAST,
      webcastId: "webcast2",
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  it("resets properly", () => {
    const domOrder = getDefaultDomOrder();
    domOrder[0] = "webcast1";
    domOrder[1] = "webcast2";
    domOrder[2] = "webcast3";
    const positionMap = getDefaultPositionMap();
    positionMap[0] = 0;
    positionMap[1] = 1;
    positionMap[2] = 2;
    const initialState = Object.assign({}, defaultState, {
      layoutId: 3,
      layoutSet: true,
      displayed: ["webcast1", "webcast2", "webcast3"],
      domOrder,
      positionMap,
    });
    const expectedState = Object.assign({}, defaultState, {
      layoutId: 3,
      layoutSet: true,
    });
    const action = {
      type: types.RESET_WEBCASTS,
    };
    expect(videoGrid_1.default(initialState, action)).toEqual(expectedState);
  });
  // Test that we can handle adding a webcast to all possible views in all possible layouts
  for (let i = 0; i < LayoutConstants_1.NUM_LAYOUTS; i++) {
    const numViewsInLayout = LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[i];
    it(`adds webcasts to all views in layout ${i}`, () => {
      const initialState = Object.assign({}, defaultState, {
        layoutId: i,
        layoutSet: true,
      });
      const domOrder = getDefaultDomOrder();
      const positionMap = getDefaultPositionMap();
      const domOrderLivescoreOn = getDefaultDomOrderLivescoreOn();
      const displayed = [];
      for (let j = 0; j < numViewsInLayout; j++) {
        domOrder[j] = `webcast${j}`;
        positionMap[j] = j;
        displayed.push(`webcast${j}`);
        domOrderLivescoreOn[j] = false;
      }
      const expectedState = Object.assign({}, initialState, {
        displayed,
        domOrder,
        positionMap,
        domOrderLivescoreOn,
      });
      let state = initialState;
      for (let k = 0; k < numViewsInLayout; k++) {
        const action = {
          type: types.ADD_WEBCAST_AT_POSITION,
          webcastId: `webcast${k}`,
          position: k,
        };
        state = videoGrid_1.default(state, action);
      }
      expect(state).toEqual(expectedState);
    });
  }
  // Test that we can't add a webcast to an invalid position in any layout
  for (let i = 0; i < LayoutConstants_1.NUM_LAYOUTS; i++) {
    it(`does not add a webcast at a location if layout ${i} cannot display it`, () => {
      const initialState = Object.assign({}, defaultState, {
        layoutId: i,
        layoutSet: true,
      });
      const invalidIndex = LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[i];
      const action = {
        type: types.ADD_WEBCAST_AT_POSITION,
        position: invalidIndex,
        webcastId: "webcast0",
      };
      expect(videoGrid_1.default(initialState, action)).toEqual(initialState);
    });
  }
});
