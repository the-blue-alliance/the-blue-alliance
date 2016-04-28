export const SET_WEBCASTS_RAW = 'SET_WEBCASTS_RAW'
export const TOGGLE_CHAT_PANEL_VISIBILITY = 'TOGGLE_CHAT_PANEL_VISIBILITY'
export const TOGGLE_HASHTAG_PANEL_VISIBILITY = 'TOGGLE_HASHTAG_PANEL_VISIBILITY'
export const ADD_WEBCAST = 'ADD_WEBCAST'
export const REMOVE_WEBCAST = 'REMOVE_WEBCAST'
export const RESET_WEBCASTS = 'RESET_WEBCASTS'
export const SET_LAYOUT = 'SET_LAYOUT'

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts) {
  return {
    type: SET_WEBCASTS_RAW,
    webcasts
  }
}

export function toggleChatPanelVisibility() {
  return {
    type: TOGGLE_CHAT_PANEL_VISIBILITY
  }
}

export function toggleHashtagPanelVisibility() {
  return {
    type: TOGGLE_HASHTAG_PANEL_VISIBILITY
  }
}

export function addWebcast(id) {
  return {
    type: ADD_WEBCAST,
    id
  }
}

export function removeWebcast(id) {
  return {
    type: REMOVE_WEBCAST,
    id
  }
}

export function resetWebcasts() {
  return {
    type: RESET_WEBCASTS
  }
}

export function setLayout(layoutId) {
  return {
    type: SET_LAYOUT,
    layoutId
  }
}
