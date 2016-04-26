import { combineReducers } from 'redux'
import webcasts from './webcasts'
import webcastsById from './webcastsById'
import chatPanelVisible from './chatPanelVisible'
import hashtagPanelVisible from './hashtagPanelVisible'
import displayedWebcasts from './displayedWebcasts'

const gamedayReducer = combineReducers({
  webcasts,
  webcastsById,
  chatPanelVisible,
  hashtagPanelVisible,
  displayedWebcasts
})

export default gamedayReducer
