export const SET_WEBCASTS_RAW = 'SET_WEBCASTS_RAW'
export const TOGGLE_CHAT_PANEL_VISIBILITY = 'TOGGLE_CHAT_PANEL_VISIBILITY'
export const TOGGLE_HASHTAG_PANEL_VISIBILITY = 'TOGGLE_HASHTAG_PANEL_VISIBILITY'

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
