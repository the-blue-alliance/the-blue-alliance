// TODO(eugene): Don't use compatibility package.
import firebase from "firebase/compat/app";
import "firebase/compat/database";
import Firedux from "firedux";
import { combineReducers } from "redux";
import chats from "./chats";
import favoriteTeams from "./favorites";
import videoGrid from "./videoGrid";
import visibility from "./visibility";
import { specialWebcastIds, webcastsById } from "./webcastsById";

// Firebase
const firebaseApp = firebase.initializeApp({
  apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
  authDomain: "tbatv-prod-hrd.firebaseapp.com",
  databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
});
const ref = firebaseApp.database().ref();
export const firedux = new Firedux({
  ref,
});

const gamedayReducer = combineReducers({
  firedux: firedux.reducer(),
  webcastsById,
  specialWebcastIds,
  visibility,
  videoGrid,
  chats,
  favoriteTeams,
});

export default gamedayReducer;
