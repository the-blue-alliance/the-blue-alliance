// Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-messaging.js');

// // Initialize the Firebase app in the service worker by passing in the
// // messagingSenderId.
// firebase.initializeApp({
//   'messagingSenderId': '836511118694'
// });
var config = {
  apiKey: "AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs",
  authDomain: "tbatv-prod-hrd.firebaseapp.com",
  databaseURL: "https://tbatv-prod-hrd.firebaseio.com",
  storageBucket: "tbatv-prod-hrd.appspot.com",
  messagingSenderId: "836511118694"
};
firebase.initializeApp(config);

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
