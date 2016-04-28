import { SET_LAYOUT } from '../actions'

const layout = (state = 0, action) => {
  switch(action.type) {
    case SET_LAYOUT:
    return action.layoutId
    default:
    return state
  }
}

export default layout
