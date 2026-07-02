// TODO(eugene): Don't use compatibility package.
import firebase from "firebase/compat/app";
import "firebase/compat/database";

// Access Firebase config from window (loaded by tba_keys.js script tag)
const emulatorHost = window.firebaseDatabaseEmulatorHost || "";
const projectId = window.firebaseProjectId || "demo-test";

// When using the emulator, construct a valid databaseURL from the emulator host
// since the emulator still needs a URL with namespace to identify the database
let databaseURL = window.firebaseDatabaseURL || "";
if (emulatorHost && !databaseURL) {
  databaseURL = `http://${emulatorHost}?ns=${projectId}`;
}

const config = {
  apiKey: window.firebaseApiKey || "",
  authDomain: window.firebaseAuthDomain || "",
  databaseURL: databaseURL,
  projectId: projectId,
  storageBucket: window.firebaseStorageBucket || "",
  messagingSenderId: window.firebaseMessagingSenderId || "",
  appId: window.firebaseAppId || "",
};

const FirebaseApp = firebase.initializeApp(config);

// Use emulator for local development if configured
if (emulatorHost) {
  const parts = emulatorHost.split(":");
  const host = parts[0];
  const port = parseInt(parts[1], 10);
  firebase.database().useEmulator(host, port);
}

export default FirebaseApp;
