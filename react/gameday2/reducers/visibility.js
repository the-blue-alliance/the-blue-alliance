import { TOGGLE_CHAT_PANEL_VISIBILITY, TOGGLE_HASHTAG_PANEL_VISIBILITY, TOGGLE_TICKER_PANEL_VISIBILITY } from '../constants/ActionTypes'

const defaultState = {
  hashtagPanel: false,
  chatPanel: false,
  tickerPanel: false
}

const toggleChatPanelVisibility = (state) => {
  return Object.assign({}, state, {
    chatPanel: !state.chatPanel
  })
}

const toggleHashtagPanelVisibility = (state) => {
  // Only show EITHER the hashtag panel OR the ticker panel, not both
  let hashtagPanelVisible = !state.hashtagPanel
  let tickerPanelVisible = state.tickerPanel ? (state.hashtagPanel) : false
  return Object.assign({}, state, {
    hashtagPanel: hashtagPanelVisible,
    tickerPanel: tickerPanelVisible
  })
}

const toggleTickerPanelVisibility = (state) => {
  // Only show EITHER the hashtag panel OR the ticker panel, not both
  let tickerPanelVisible = !state.tickerPanel
  let hashtagPanelVisible = state.hashtagPanel ? (state.tickerPanel) : false
  return Object.assign({}, state, {
    tickerPanel: tickerPanelVisible,
    hashtagPanel: hashtagPanelVisible
  })
}

const visibility = (state = defaultState, action) => {
  switch(action.type) {
    case TOGGLE_CHAT_PANEL_VISIBILITY:
    return toggleChatPanelVisibility(state)
    case TOGGLE_HASHTAG_PANEL_VISIBILITY:
    return toggleHashtagPanelVisibility(state)
    case TOGGLE_TICKER_PANEL_VISIBILITY:
    return toggleTickerPanelVisibility(state)
    default:
    return state
  }
}

export default visibility
