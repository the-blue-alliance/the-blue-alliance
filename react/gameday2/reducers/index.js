import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import displayedWebcasts from './displayedWebcasts'
import visibility from './visibility'
import layout from './layout'
import videoGrid from './videoGrid'

const gamedayReducer = combineReducers({
  webcastsById,
  visibility,
  displayedWebcasts,
  layout,
  videoGrid,
})

export default gamedayReducer
