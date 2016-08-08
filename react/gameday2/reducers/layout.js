import { SET_LAYOUT } from '../constants/ActionTypes'

const defaultState = {
  layoutId: 0,
  layoutSet: false,
}

const layout = (state = defaultState, action) => {
  switch (action.type) {
    case SET_LAYOUT:
      return {
        layoutId: action.layoutId,
        layoutSet: true,
      }
    default:
      return state
  }
}

export default layout
