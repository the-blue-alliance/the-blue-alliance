import { combineReducers } from 'redux'
import webcasts from './webcasts'
import webcastsById from './webcastsById'

const gamedayReducer = combineReducers({
  webcasts,
  webcastsById
})

export default gamedayReducer
