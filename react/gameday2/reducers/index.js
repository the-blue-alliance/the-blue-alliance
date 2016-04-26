import { combineReducers } from 'redux'
import webcasts from './webcasts'
import webcastsById from './webcastsById'
import chatPanelVisible from './chatPanelVisible'
import hashtagPanelVisible from './hashtagPanelVisible'

const gamedayReducer = combineReducers({
  webcasts,
  webcastsById,
  chatPanelVisible,
  hashtagPanelVisible
})

export default gamedayReducer
