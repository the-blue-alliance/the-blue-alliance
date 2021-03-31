#! /bin/bash
# Create tba_keys.js from environment secrets
        touch ./static/javascript/tba_js/tba_keys.js
        cat >./static/javascript/tba_js/tba_keys.js <<EOF
var firebaseApiKey = "${FIREBASE_API_KEY}";
var firebaseAppId = "${FIREBASE_APP_ID}";
var firebaseAuthDomain = "${GCLOUD_PROJECT_ID}.firebaseapp.com";
var firebaseDatabaseURL = "https://${GCLOUD_PROJECT_ID}.firebaseio.com";
var firebaseStorageBucket = "${GCLOUD_PROJECT_ID}.appspot.com";
var firebaseMessagingSenderId = "${FIREBASE_MESSAGING_SENDER_ID}";
var firebaseProjectId = "${GCLOUD_PROJECT_ID}";
EOF
