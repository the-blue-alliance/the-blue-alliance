import { TOGGLE_CHAT_PANEL_VISIBILITY, TOGGLE_HASHTAG_PANEL_VISIBILITY, TOGGLE_TICKER_PANEL_VISIBILITY } from '../constants/ActionTypes'

const defaultState = {
  hashtagPanel: false,
  chatPanel: false,
  tickerPanel: false
}

const visibility = (state = defaultState, action) => {
  switch(action.type) {
    case TOGGLE_CHAT_PANEL_VISIBILITY:
    return Object.assign({}, state, {
      chatPanel: !state.chatPanel
    })
    case TOGGLE_HASHTAG_PANEL_VISIBILITY:
    // Only show EITHER the hashtag panel OR the ticker panel, not both
    let hashtagPanelVisible = !state.hashtagPanel
    return Object.assign({}, state, {
      hashtagPanel: hashtagPanelVisible,
      tickerPanel: !hashtagPanelVisible
    })
    case TOGGLE_TICKER_PANEL_VISIBILITY:
    // Only show EITHER the hashtag panel OR the ticker panel, not both
    let tickerPanelVisible = !state.tickerPanel
    return Object.assign({}, state, {
      tickerPanel: tickerPanelVisible,
      hashtagPanel: !tickerPanelVisible
    })
    default:
    return state
  }
}

export default visibility
