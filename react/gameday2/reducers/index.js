import Firebase from 'firebase'
import Firedux from 'firedux'
import { combineReducers } from 'redux'
import webcastsById from './webcastsById'
import visibility from './visibility'
import videoGrid from './videoGrid'
import chats from './chats'

// Firebase
var firebaseApp = Firebase.initializeApp({
  apiKey: 'AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs',
  authDomain: 'tbatv-prod-hrd.firebaseapp.com',
  databaseURL: 'https://tbatv-prod-hrd.firebaseio.com'
})
var ref = firebaseApp.database().ref()
export const firedux = new Firedux({
  ref,
})

const gamedayReducer = combineReducers({
  firedux: firedux.reducer(),
  webcastsById,
  visibility,
  videoGrid,
  chats,
})

export default gamedayReducer
