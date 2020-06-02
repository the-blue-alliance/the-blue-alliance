import Firebase from 'firebase'

const FirebaseApp = Firebase.initializeApp({
  apiKey: 'AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs',
  authDomain: 'tbatv-prod-hrd.firebaseapp.com',
  databaseURL: 'https://tbatv-prod-hrd.firebaseio.com',
})

export default FirebaseApp
