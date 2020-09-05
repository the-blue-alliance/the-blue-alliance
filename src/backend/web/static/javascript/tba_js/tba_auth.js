function signInWithGoogle(csrfToken) {
  var provider = new firebase.auth.GoogleAuthProvider();
  provider.addScope("email");
  provider.addScope("profile");
  _signInWithProvider(provider, csrfToken);
}

function signInWithApple(csrfToken) {
   var provider = new firebase.auth.OAuthProvider("apple.com");
   provider.addScope("email");
   provider.addScope("name");
   _signInWithProvider(provider, csrfToken);
}

function _signInWithProvider(provider, csrfToken) {
  // As httpOnly cookies are to be used, do not persist any state client side.
  firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);
  firebase.auth().signInWithPopup(provider).then(function(userCredential) {
    var user = userCredential.user;
    user.getIdToken().then(function(idToken) {
      if (!idToken) {
        _showSignInError("Unable to get id token");
        return;
      }
      $.ajax({
        type: 'POST',
        url: '/account/login',
        dataType: 'json',
        headers: {
          'X-CSRFToken': csrfToken
        },
        data: {'id_token': idToken},
        success: function(data, status) {
          if (status == "success") {
            // Session successfully created - redirect
            var urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has("next")) {
              window.location.assign(urlParams.get("next"));
            } else {
              window.location.assign("/account");
            }
          } else {
            _showSignInError("Unable to create session cookie");
          }
        },
        error: function(data, status) {
          _showSignInError(status);
        }
      });
    }).catch(function(error) {
      _showSignInError(error);
    });
  }, function(error) {
    _showSignInError(error);
  }).catch(function(error) {
    _showSignInError(error);
  });
}

function _showSignInError(error) {
   alert("Error logging in - " + error);
   console.error(error);
}
