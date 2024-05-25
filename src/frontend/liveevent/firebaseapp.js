// TODO(eugene): Don't use compatibility package.
import firebase from "firebase/compat/app";
import "firebase/compat/database";

const FirebaseApp = firebase.initializeApp({
  apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
  authDomain: "tbatv-prod-hrd.firebaseapp.com",
  databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
});

export default FirebaseApp;
