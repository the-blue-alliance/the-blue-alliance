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

// Connect to database emulator if available
// Set firebaseDatabaseEmulatorHost in tba_keys.js (e.g., "localhost:9000")
if (firebaseDatabaseEmulatorHost) {
  var parts = firebaseDatabaseEmulatorHost.split(':');
  var host = parts[0];
  var port = parseInt(parts[1], 10);
  firebase.database().useEmulator(host, port);
}