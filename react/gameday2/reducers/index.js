import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import displayedWebcasts from './displayedWebcasts'
import visibility from './visibility'
import layout from './layout'

const gamedayReducer = combineReducers({
  webcastsById,
  visibility,
  displayedWebcasts,
  layout,
})

export default gamedayReducer
