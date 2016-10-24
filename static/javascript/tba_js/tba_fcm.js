const messaging = firebase.messaging();

// Setup messaging if logged in and permission granted, or if logged in and forced
function setupMessaging(forceRequestPermission) {
  $(".notifications-enabled-visible").hide();
  $(".notifications-disabled-visible").show();
  if (Notification.permission == 'denied' && forceRequestPermission) {
    alert("You have blocked push notifications in your browser for this site. Please unblock and try again.");  // TODO show more elegantly
  } else if ((Notification.permission == 'granted' && !window.localStorage.getItem('TBA_notificationsPermission') == 'disabled') || forceRequestPermission) {
    $.ajax({
      type: 'GET',
      url: '/_/account/info',
    }).done(function(accountInfo) {
      if (accountInfo.logged_in) {
        if (accountInfo.user_id != window.localStorage.getItem('TBA_lastFCMTokenUserId')) {
          console.log('[TBA FCM] Different user logged in. Can\'t use same token.');

          messaging.requestPermission()
          .then(function() {
            return messaging.getToken();
          })
          .then(function(token) {
            console.log('[TBA FCM] Deleting token:', token);
            messaging.deleteToken(token)
            .then(function() {
              console.log('[TBA FCM] Token successfully deleted!')
              setupMessagingHelper(accountInfo);
            })
            .catch(function(err) {
              console.log('[TBA FCM] Unable to delete token token. Cannot continue with FCM setup.', err);
            });
          })
          .catch(function(err) {
            console.log('[TBA FCM] Unable to get permission to delete token. Cannot continue with FCM setup.', err);
          });
        } else {
          setupMessagingHelper(accountInfo);
        }
      }
    });
  }
}
setupMessaging(false);  // Always attempt to setup messaging without forcing

function setupMessagingHelper(accountInfo) {
  messaging.requestPermission()
  .then(function() {
    return messaging.getToken();
  })
  .then(function(token) {
    console.log('[TBA FCM] Token:', token);
    sendTokenToServer(accountInfo, token);
    $(".notifications-enabled-visible").show();
    $(".notifications-disabled-visible").hide();
    window.localStorage.setItem('TBA_notificationsPermission', 'enabled');
  })
  .catch(function(err) {
    console.log('[TBA FCM] Unable to get permission to setup messaging. ', err);
  });

  messaging.onTokenRefresh(function() {
    messaging.getToken()
    .then(function(refreshedToken) {
      console.log('[TBA FCM] Token refreshed:', refreshedToken);
      sendTokenToServer(accountInfo, refreshedToken);
    })
    .catch(function(err) {
      console.log('[TBA FCM] Unable to retrieve refreshed token. ', err);
    });
  });

  messaging.onMessage(function(payload) {
    console.log("[TBA FCM] Message received. ", payload);
  });
}

function disableMessaging() {
  messaging.requestPermission()
  .then(function() {
    return messaging.getToken();
  })
  .then(function(token) {
    console.log('[TBA FCM] Deleting token:', token);
    messaging.deleteToken(token);
    $(".notifications-enabled-visible").hide();
    $(".notifications-disabled-visible").show();
    window.localStorage.setItem('TBA_notificationsPermission', 'disabled');
  })
  .catch(function(err) {
    console.log('[TBA FCM] Unable to delete token token. Cannot disable messaging.', err);
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
  // UUIDs are unique per device, so different logins on the same device may share the same UUID
  var uuid = window.localStorage.getItem('TBA_UUID');
  if (uuid == null) {
    uuid = generateUUID();
    window.localStorage.setItem('TBA_UUID', uuid);
  }
  return uuid
}

function sendTokenToServer(accountInfo, token) {
  window.localStorage.setItem('TBA_lastFCMTokenUserId', accountInfo.user_id);
  if (token != window.localStorage.getItem('TBA_FCMTokenSentToServer')) {
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
      window.localStorage.setItem('TBA_FCMTokenSentToServer', token);
      console.log("[TBA FCM] Token sent to server!")
    });
  } else {
    console.log("[TBA FCM] Server already has latest token.")
  }
}
