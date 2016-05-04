import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import chatPanelVisible from './chatPanelVisible'
import hashtagPanelVisible from './hashtagPanelVisible'
import displayedWebcasts from './displayedWebcasts'
import layout from './layout'

const gamedayReducer = combineReducers({
  webcastsById,
  chatPanelVisible,
  hashtagPanelVisible,
  displayedWebcasts,
  layout
})

export default gamedayReducer
