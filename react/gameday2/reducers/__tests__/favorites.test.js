import favorites from '../favorites'
import { SET_FAVORITE_TEAMS } from '../../constants/ActionTypes'

describe('favorites reducer', () => {
  const defaultState = new Set()

  it('defaults to an empty Set', () => {
    expect(favorites(undefined, {})).toEqual(defaultState)
  })

  it('sets favorites for the SET_FAVORITE_TEAMS action', () => {
    const initialState = Object.assign({}, defaultState)

    const favoriteTeams = [
      {
        model_key: 'frc148',
      }, {
        model_key: 'frc111',
      }, {
        model_key: 'frc2056',
      },
    ]

    const expectedState = new Set()
    favoriteTeams.forEach((team) => expectedState.add(team.model_key))

    const action = {
      type: SET_FAVORITE_TEAMS,
      favoriteTeams,
    }

    expect(favorites(initialState, action)).toEqual(expectedState)
  })
})
