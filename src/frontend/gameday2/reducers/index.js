// TODO(eugene): Don't use compatibility package.
import firebase from "firebase/compat/app";
import "firebase/compat/database";
import FirebaseMirror from "../firebaseMirror";
import { combineReducers } from "redux";
import { webcastsById, specialWebcastIds } from "./webcastsById";
import visibility from "./visibility";
import videoGrid from "./videoGrid";
import chats from "./chats";
import favoriteTeams from "./favorites";

// Firebase
const firebaseApp = firebase.initializeApp({
  apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
  authDomain: "tbatv-prod-hrd.firebaseapp.com",
  databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
});
const ref = firebaseApp.database().ref();
export const firebaseMirror = new FirebaseMirror({
  ref,
});

const gamedayReducer = combineReducers({
  firebaseMirror: firebaseMirror.reducer(),
  webcastsById,
  specialWebcastIds,
  visibility,
  videoGrid,
  chats,
  favoriteTeams,
});

export default gamedayReducer;
