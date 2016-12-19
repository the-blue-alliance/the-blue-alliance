import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import visibility from './visibility'
import videoGrid from './videoGrid'

const gamedayReducer = combineReducers({
  webcastsById,
  visibility,
  videoGrid,
})

export default gamedayReducer
