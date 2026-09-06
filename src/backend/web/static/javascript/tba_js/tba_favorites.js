var favoriteTeamsCookieName = "tba-favorite-teams";
var cachedCsrfToken = null;

function withCsrfToken(success, error) {
  /*
  Fetches a CSRF token for the current session and hands it to success().
  The token cannot be embedded in the page because team/event pages are
  publicly cached, so every visitor would receive whichever token happened to
  warm the cache. See /_/account/info.
  */
  if (cachedCsrfToken != null) {
    success(cachedCsrfToken);
    return;
  }
  $.ajax({
    type: 'GET',
    dataType: 'json',
    url: '/_/account/info',
    timeout: 10000,  // 10s
    success: function(data, textStatus, xhr) {
      cachedCsrfToken = data['csrf_token'];
      success(cachedCsrfToken);
    },
    error: error
  });
}

function updateFavoriteTeams(teamKey, action, skipDelay, csrfToken, isCsrfRetry) {
  /*
  Updates Favorites locally and on the server and
  updates the page to reflect these changes
  teamKey: like "frc254" or null
  action: "add" or "delete" or null (doesn't do anything if teamKey is null)
  */
  var storedFavoriteTeams = getLocalFavoriteTeams();

  if (teamKey != null) {
    if (action == 'add') {
      $.ajax({
        type: 'POST',
        url: '/_/account/favorites/add',
        data: {'model_key': teamKey, 'model_type': 1},
        headers: {
          'X-CSRFToken': csrfToken
        },
        timeout: 10000,  // 10s
        success: function(data, textStatus, xhr) {
          addLocalFavoriteTeam(teamKey);
          updateFavoriteTeams(null, null, false);
        },
        error: function(xhr, textStatus, errorThrown) {
          handleFavoriteError(xhr, teamKey, 'add', isCsrfRetry);
        }
      });
    } else if (action == 'delete') {
      $.ajax({
        type: 'POST',
        url: '/_/account/favorites/delete',
        data: {'model_key': teamKey, 'model_type': 1},
        headers: {
          'X-CSRFToken': csrfToken
        },
        timeout: 10000,  // 10s
        success: function(data, textStatus, xhr) {
          deleteLocalFavoriteTeam(teamKey);
          updateFavoriteTeams(null, null, false);
        },
        error: function(xhr, textStatus, errorThrown) {
          handleFavoriteError(xhr, teamKey, 'delete', isCsrfRetry);
        }
      });
    }
  } else {
    if (storedFavoriteTeams == null) {
      $.ajax({
        type: 'GET',
        dataType: 'json',
        url: '/_/account/favorites/1',
        success: function(favorites, textStatus, xhr) {
          var favoriteTeams = {};
          for (var key in favorites) {
            favoriteTeams[favorites[key]['model_key']] = true;
          }
          setLocalFavoriteTeams(favoriteTeams);
          updatePageFavoriteTeams(favoriteTeams, skipDelay);
        },
        error: function(xhr, textStatus, errorThrown) {
          updatePageFavoriteTeams({}, skipDelay);
        }
      });
    } else {
      updatePageFavoriteTeams(storedFavoriteTeams, skipDelay);
    }
  }
}

function handleFavoriteError(xhr, teamKey, action, isCsrfRetry) {
  /*
  Handles a failed favorites POST.

  A CSRF token is only valid for WTF_CSRF_TIME_LIMIT (one hour by default), but
  cachedCsrfToken lives as long as the page does. A tab left open past that
  limit would otherwise keep POSTing the same expired token and fail forever,
  so on a 400 we drop the cached token, fetch a fresh one, and retry once.
  */
  if (xhr.status == 401) {
    $('#login-modal').modal('show');
  } else if (xhr.status == 400 && !isCsrfRetry) {
    cachedCsrfToken = null;
    withCsrfToken(function(csrfToken) {
      updateFavoriteTeams(teamKey, action, false, csrfToken, true);
    }, function(xhr, textStatus, errorThrown) {
      showFavoriteError(action);
      updateFavoriteTeams(null, null, false);
    });
    return;
  } else {
    showFavoriteError(action);
  }
  updateFavoriteTeams(null, null, false);
}

function getLocalFavoriteTeams() {
  return JSON.parse($.cookie(favoriteTeamsCookieName));
}

function setLocalFavoriteTeams(favoriteTeams) {
  var date = new Date();
  date.setTime(date.getTime() + (5 * 60 * 1000));  // Set 5 minutes cookie expiration
  $.cookie(favoriteTeamsCookieName, JSON.stringify(favoriteTeams), {expires: date, path: '/'});
}

function addLocalFavoriteTeam(teamKey) {
  var storedFavoriteTeams = getLocalFavoriteTeams();
  if (storedFavoriteTeams != null) {
    storedFavoriteTeams[teamKey] = true;
    setLocalFavoriteTeams(storedFavoriteTeams);
  }
}

function deleteLocalFavoriteTeam(teamKey) {
  var storedFavoriteTeams = getLocalFavoriteTeams();
  if (storedFavoriteTeams != null && teamKey in storedFavoriteTeams) {
    delete storedFavoriteTeams[teamKey];
    setLocalFavoriteTeams(storedFavoriteTeams);
  }
}

function updatePageFavoriteTeams(favoriteTeams, skipDelay) {
  updateMatchFavoriteTeams(favoriteTeams);
  updateTeamlistFavoriteTeams(favoriteTeams);
  if (skipDelay) {
    updateTeamFABFavoriteTeams(favoriteTeams);
  } else {
    setTimeout(function() {updateTeamFABFavoriteTeams(favoriteTeams)}, 3000);
  }
}

function updateMatchFavoriteTeams(favoriteTeams) {
  // Reset all stars
  $(".favorite-match-icon").each(function() {
    $(this).hide();
  });

  $(".favorite-team-dot").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();  // Dot
      var match_key = $(this).attr("data-match");
      $('.favorite-match-icon-' + match_key).show();  // Star
    } else {
      $(this).hide();  // Dot
    }
  });
}

function updateTeamlistFavoriteTeams(favoriteTeams) {
  $(".favorite-team-icon").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();
    } else {
      $(this).hide();
    }
  });
}

function updateTeamFABFavoriteTeams(favoriteTeams) {
  $(".tba-fab-team").each(function() {
    $(this).find(".tba-spinner").remove();
    $(this).prop("disabled", false);
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).find(".not-favorite").hide();
      $(this).find(".favorite").show();
      setupFavDeleteClick();
    } else {
      $(this).find(".favorite").hide();
      $(this).find(".not-favorite").show();
      setupFavAddClick();
    }
  });
}

function setupFavClick(action, hideSelector) {
  $(".tba-fab-team").off("click");  // make sure only one click handler is attached at a time
  $(".tba-fab-team").click(function() {
    $(".tba-fab-team").off("click");
    $(this).find(hideSelector).hide();
    addSpinner($(this));

    var teamKey = $(this).attr("data-team");
    withCsrfToken(function(csrfToken) {
      updateFavoriteTeams(teamKey, action, false, csrfToken);
    }, function(xhr, textStatus, errorThrown) {
      showFavoriteError(action);
      updateFavoriteTeams(null, null, false);
    });
  });
}

function setupFavAddClick() {
  setupFavClick('add', ".not-favorite");
}

function setupFavDeleteClick() {
  setupFavClick('delete', ".favorite");
}

function showFavoriteError(action) {
  var verb = (action == 'delete') ? 'delete' : 'add';
  $('#fixed-alert-container').append('<div class="alert alert-danger alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to ' + verb + ' favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
}

function addSpinner(el) {
  el.append("<span class='tba-spinner'></span>");
  el.prop("disabled", true);
}

$(document).ready(function(){
  // Setup redirect after login
  $('#mytba-login').click(function() {
    window.location.href = '/login?redirect=' + escape('/account/register?redirect=' + document.URL.replace(document.location.origin, ""));
  });

  setupFavAddClick();
  updateFavoriteTeams(null, null, true);
});
