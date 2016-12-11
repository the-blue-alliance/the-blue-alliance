/* eslint-disable max-len */
import {
  TOGGLE_CHAT_SIDEBAR_VISIBILITY,
  TOGGLE_HASHTAG_SIDEBAR_VISIBILITY,
  TOGGLE_LAYOUT_DRAWER_VISIBILITY,
  SET_LAYOUT_DRAWER_VISIBILITY,
} from '../constants/ActionTypes'
/* eslint-enable max-len */

const defaultState = {
  hashtagSidebar: false,
  chatSidebar: false,
  chatSidebarHasBeenVisible: false,
  tickerSidebar: false,
  layoutDrawer: false,
}

const toggleChatSidebarVisibility = (state) => {
  const hasBeenVisible = (state.chatSidebarHasBeenVisible || !state.chatSidebar)
  return Object.assign({}, state, {
    chatSidebar: !state.chatSidebar,
    chatSidebarHasBeenVisible: hasBeenVisible,
  })
}

const toggleHashtagSidebarVisibility = (state) => (Object.assign({}, state, {
  hashtagSidebar: !state.hashtagSidebar,
}))

const toggleLayoutDrawerVisibility = (state) => (Object.assign({}, state, {
  layoutDrawer: !state.layoutDrawer,
}))

const setLayoutDrawerVisibility = (visibility, state) => (Object.assign({}, state, {
  layoutDrawer: !state.layoutDrawer,
}))

const visibility = (state = defaultState, action) => {
  switch (action.type) {
    case TOGGLE_CHAT_SIDEBAR_VISIBILITY:
      return toggleChatSidebarVisibility(state)
    case TOGGLE_HASHTAG_SIDEBAR_VISIBILITY:
      return toggleHashtagSidebarVisibility(state)
    case TOGGLE_LAYOUT_DRAWER_VISIBILITY:
      return toggleLayoutDrawerVisibility(state)
    case SET_LAYOUT_DRAWER_VISIBILITY:
      return setLayoutDrawerVisibility(action.visible, state)
    default:
      return state
  }
}

export default visibility
