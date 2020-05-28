import Firebase from 'firebase'
import Firedux from 'firedux'
import { combineReducers } from 'redux'
import { webcastsById, specialWebcastIds } from './webcastsById'
import visibility from './visibility'
import videoGrid from './videoGrid'
import chats from './chats'
import favoriteTeams from './favorites'

// Firebase
const firebaseApp = Firebase.initializeApp({
  apiKey: 'AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs',
  authDomain: 'tbatv-prod-hrd.firebaseapp.com',
  databaseURL: 'https://tbatv-prod-hrd.firebaseio.com',
})
const ref = firebaseApp.database().ref()
export const firedux = new Firedux({
  ref,
})

const gamedayReducer = combineReducers({
  firedux: firedux.reducer(),
  webcastsById,
  specialWebcastIds,
  visibility,
  videoGrid,
  chats,
  favoriteTeams,
})

export default gamedayReducer
