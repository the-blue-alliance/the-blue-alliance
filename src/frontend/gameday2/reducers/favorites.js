"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ActionTypes_1 = require("../constants/ActionTypes");
const defaultState = new Set();
const setFavoriteTeams = (favoriteTeams) => {
  const favoriteTeamsSet = new Set();
  favoriteTeams.forEach((favoriteTeam) =>
    favoriteTeamsSet.add(favoriteTeam.model_key)
  );
  return favoriteTeamsSet;
};
const favoriteTeams = (state = defaultState, action) => {
  switch (action.type) {
    case ActionTypes_1.SET_FAVORITE_TEAMS:
      return setFavoriteTeams(action.favoriteTeams);
    default:
      return state;
  }
};
exports.default = favoriteTeams;
