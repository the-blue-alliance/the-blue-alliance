// Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in the
// messagingSenderId.
firebase.initializeApp({
  'messagingSenderId': firebaseMessagingSenderId
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();

// If you would like to customize notifications that are received in the
// background (Web app is closed or not in browser focus) then you should
// implement this optional method.
messaging.setBackgroundMessageHandler(function(payload) {
  console.log('[TBA FCM SW] Received background message.');

  // Check for login
  fetch('/_/account/info', {credentials: 'include'})
  .then(function (response) {
    response.json().then(function (accountInfo) {
      if (accountInfo.logged_in) {
        console.log('[TBA FCM SW] Message:', payload);

        buildAndShowNotification(self.registration, payload);
      } else {
        console.log("[TBA FCM SW] Not logged in! Deleting token...");

        messaging.getToken()
        .then(function(token) {
          console.log('[TBA FCM SW] Deleting token:', token);
          messaging.deleteToken(token)
          .then(function() {
            console.log('[TBA FCM SW] Token successfully deleted!')
          })
          .catch(function(err) {
            console.log('[TBA FCM SW] Unable to delete token token.', err);
          });
        })
        .catch(function(err) {
          console.log('[TBA FCM SW] Unable to get permission to delete token.', err);
        });
      }
    });
  })
  .catch(function (err) {
    console.log("[TBA FCM SW] Error checking for login status!", err);
  });
});

function buildAndShowNotification(registration, payload) {
  const message_type = payload.data.message_type;
  const message_data = JSON.parse(payload.data.message_data);

  var notificationTitle = null;
  var notificationOptions = null;
  if (message_type == 'ping') {
    notificationTitle = message_data.title;
    notificationOptions = {
      body: message_data.desc,
      icon: '/images/logo_square_512.png'
    };
  } else if (message_type == 'match_score') {  // TODO: incomplete
    notificationTitle = message_data.match.key + ' Results';
    notificationOptions = {
      body: 'TODO',
      icon: '/images/logo_square_512.png'
    };
  } else {  // TODO: support other notifications
    return;
  }
  registration.showNotification(notificationTitle, notificationOptions);
}
