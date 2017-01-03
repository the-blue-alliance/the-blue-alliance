import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import visibility from './visibility'
import videoGrid from './videoGrid'
import chats from './chats'

const gamedayReducer = combineReducers({
  webcastsById,
  visibility,
  videoGrid,
  chats,
})

export default gamedayReducer
