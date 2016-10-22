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
// [START background_handler]
messaging.setBackgroundMessageHandler(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);

  const messageData = JSON.parse(payload.data.message_data);
  const notificationTitle = messageData.title;
  const notificationOptions = {
    body: messageData.desc,
    icon: '/images/logo_square_200.png'
  };

  return self.registration.showNotification(notificationTitle,
      notificationOptions);
});
// [END background_handler]
