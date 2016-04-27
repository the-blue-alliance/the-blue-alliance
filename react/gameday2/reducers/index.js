import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import chatPanelVisible from './chatPanelVisible'
import hashtagPanelVisible from './hashtagPanelVisible'
import displayedWebcasts from './displayedWebcasts'

const gamedayReducer = combineReducers({
  webcastsById,
  chatPanelVisible,
  hashtagPanelVisible,
  displayedWebcasts
})

export default gamedayReducer
