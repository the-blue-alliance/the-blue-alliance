import { TOGGLE_CHAT_PANEL_VISIBILITY } from '../constants/ActionTypes'

const chatPanelVisibility = (state = false, action) => {
  switch(action.type) {
    case TOGGLE_CHAT_PANEL_VISIBILITY:
    return !state
    default:
    return state
  }
}

export default chatPanelVisibility
