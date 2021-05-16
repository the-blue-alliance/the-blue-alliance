"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const favorites_1 = __importDefault(require("../favorites"));
const ActionTypes_1 = require("../../constants/ActionTypes");
describe("favorites reducer", () => {
  const defaultState = new Set();
  it("defaults to an empty Set", () => {
    expect(favorites_1.default(undefined, {})).toEqual(defaultState);
  });
  it("sets favorites for the SET_FAVORITE_TEAMS action", () => {
    const initialState = Object.assign({}, defaultState);
    const favoriteTeams = [
      {
        model_key: "frc148",
      },
      {
        model_key: "frc111",
      },
      {
        model_key: "frc2056",
      },
    ];
    const expectedState = new Set();
    favoriteTeams.forEach((team) => expectedState.add(team.model_key));
    const action = {
      type: ActionTypes_1.SET_FAVORITE_TEAMS,
      favoriteTeams,
    };
    expect(favorites_1.default(initialState, action)).toEqual(expectedState);
  });
});
