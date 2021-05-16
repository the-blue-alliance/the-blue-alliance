import { SET_FAVORITE_TEAMS } from "../constants/ActionTypes";

const defaultState = new Set();

const setFavoriteTeams = (favoriteTeams: any) => {
  const favoriteTeamsSet = new Set();
  favoriteTeams.forEach((favoriteTeam: any) =>
    favoriteTeamsSet.add(favoriteTeam.model_key)
  );
  return favoriteTeamsSet;
};

const favoriteTeams = (state = defaultState, action: any) => {
  switch (action.type) {
    case SET_FAVORITE_TEAMS:
      return setFavoriteTeams(action.favoriteTeams);
    default:
      return state;
  }
};

export default favoriteTeams;
