import firebase from "firebase/app";
import "firebase/database";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'fire... Remove this comment to see the full error message
import Firedux from "firedux";
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
// @ts-expect-error(TS2339)
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
