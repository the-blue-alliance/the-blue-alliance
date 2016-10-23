// Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.5.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in the
// messagingSenderId.
firebase.initializeApp({
  'messagingSenderId': '836511118694'
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

        const messageData = JSON.parse(payload.data.message_data);
        const notificationTitle = messageData.title;
        const notificationOptions = {
          body: messageData.desc,
          icon: '/images/logo_square_200.png'
        };
        return self.registration.showNotification(notificationTitle,
          notificationOptions);
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
