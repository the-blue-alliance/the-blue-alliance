import {
  SET_FAVORITE_TEAMS,
} from '../constants/ActionTypes'

const defaultState = new Set()

const setFavoriteTeams = (favoriteTeams, state) => {
  var favoriteTeamsSet = new Set()
  for (var i in favoriteTeams) {
    favoriteTeamsSet.add(favoriteTeams[i].model_key)
  }
  return favoriteTeamsSet
}

const favoriteTeams = (state = defaultState, action) => {
  switch (action.type) {
    case SET_FAVORITE_TEAMS:
      return setFavoriteTeams(action.favoriteTeams, state)
    default:
      return state
  }
}

export default favoriteTeams
