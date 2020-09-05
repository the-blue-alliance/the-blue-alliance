set -e

npx -p less@3.11.3 lessc src/backend/web/static/css/less_css/tba_style.main.less src/build/temp/tba_style.main.css

# Create tba_keys.js from environment secrets
touch ./src/backend/web/static/javascript/tba_js/tba_keys.js
cat > ./src/backend/web/static/javascript/tba_js/tba_keys.js <<EOF
var firebaseApiKey = "${FIREBASE_API_KEY}";
var firebaseAuthDomain = "${GCLOUD_PROJECT_ID}.firebaseapp.com";
var firebaseDatabaseURL = "https://${GCLOUD_PROJECT_ID}.firebaseio.com";
var firebaseStorageBucket = "${GCLOUD_PROJECT_ID}.appspot.com";
var firebaseMessagingSenderId = "${FIREBASE_MESSAGING_SENDER_ID}";
var firebaseProjectId = "${GCLOUD_PROJECT_ID}";
EOF

python ./ops/build/do_compress.py
npm run build
