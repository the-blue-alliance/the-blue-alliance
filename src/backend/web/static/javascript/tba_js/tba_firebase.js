// Init Firebase
var config = {
  apiKey: firebaseApiKey,
  authDomain: firebaseAuthDomain,
  databaseURL: firebaseDatabaseURL,
  projectId: firebaseProjectId,
  storageBucket: firebaseStorageBucket,
  messagingSenderId: firebaseMessagingSenderId,
  appId: firebaseAppId
};
firebase.initializeApp(config);

const auth = firebase.auth();
auth.setPersistence(firebase.auth.Auth.Persistence.NONE);