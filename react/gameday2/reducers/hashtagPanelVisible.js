import { TOGGLE_HASHTAG_PANEL_VISIBILITY } from '../actions/actions'

const hashtagPanelVisibility = (state = false, action) => {
  switch(action.type) {
    case TOGGLE_HASHTAG_PANEL_VISIBILITY:
    return !state
    default:
    return state
  }
}

export default hashtagPanelVisibility
