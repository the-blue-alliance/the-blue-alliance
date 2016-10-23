// Setup messaging if logged in
$.ajax({
  type: 'GET',
  url: '/_/account/info',
}).done(function(accountInfo) {
  if (accountInfo.logged_in) {
    setupMessaging();
  }
});

function setupMessaging() {
  const messaging = firebase.messaging();
  messaging.requestPermission()
  .then(function() {
    console.log('[TBA FCM] Notification permission granted.');
    return messaging.getToken();
  })
  .then(function(token) {
    console.log('[TBA FCM] Token: ', token);
    sendTokenToServer(token);
  })
  .catch(function(err) {
    console.log('[TBA FCM] Unable to get permission to notify. ', err);
  });

  messaging.onTokenRefresh(function() {
    messaging.getToken()
    .then(function(refreshedToken) {
      console.log('[TBA FCM] Token refreshed.');
      sendTokenToServer(refreshedToken);
    })
    .catch(function(err) {
      console.log('[TBA FCM] Unable to retrieve refreshed token. ', err);
    });
  });

  messaging.onMessage(function(payload) {
    console.log("[TBA FCM] Message received. ", payload);
  });
}

// Helper functions
function generateUUID() {
  // From http://stackoverflow.com/a/8809472
  var d = new Date().getTime();
  var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = (d + Math.random()*16)%16 | 0;
    d = Math.floor(d/16);
    return (c=='x' ? r : (r&0x3|0x8)).toString(16);
  });
  return uuid;
};

function getUUID() {
  var uuid = window.localStorage.getItem('TBAUUID');
  if (uuid == null) {
    uuid = generateUUID();
    window.localStorage.setItem('TBAUUID', uuid);
  }
  return uuid
}

function sendTokenToServer(token) {
  if (token != window.localStorage.getItem('FCMTokenSentToServer')) {
    console.log('[TBA FCM] Sending token to server...');

    var display_name = jscd.browser + ' ' + jscd.browserMajorVersion +
      ' on ' + jscd.os + ' ' + jscd.osVersion;

    $.ajax({
      type: 'POST',
      url: '/_/account/register_fcm_token',
      data: {
        'fcm_token': token,
        'uuid': getUUID(),
        'display_name': display_name,
      }
    }).done(function() {
      window.localStorage.setItem('FCMTokenSentToServer', token);
      console.log("[TBA FCM] Token sent to server!")
    });
  } else {
    console.log("[TBA FCM] Server already has latest token.")
  }
}
