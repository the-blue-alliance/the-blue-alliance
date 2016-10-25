var favoriteTeamsCookieName = "tba-favorite-teams";

function updateFavoriteTeams(teamKey, action, skipDelay) {
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
        timeout: 10000,  // 10s
        success: function(data, textStatus, xhr) {
          addLocalFavoriteTeam(teamKey);
          updateFavoriteTeams(null, null, false);
        },
        error: function(xhr, textStatus, errorThrown) {
          if (xhr.status == 401) {
            $('#login-modal').modal('show');
          } else {
            $('#fixed-alert-container').append('<div class="alert alert-danger alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to add favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
          }
          updateFavoriteTeams(null, null, false);
        }
      });
    } else if (action == 'delete') {
      $.ajax({
        type: 'POST',
        url: '/_/account/favorites/delete',
        data: {'model_key': teamKey, 'model_type': 1},
        timeout: 10000,  // 10s
        success: function(data, textStatus, xhr) {
          deleteLocalFavoriteTeam(teamKey);
          updateFavoriteTeams(null, null, false);
        },
        error: function(xhr, textStatus, errorThrown) {
          if (xhr.status == 401) {
            $('#login-modal').modal('show');
          } else {
            $('#fixed-alert-container').append('<div class="alert alert-danger alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to delete favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
          }
          updateFavoriteTeams(null, null, false);
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
    $(this).find(".fa-spin").remove();
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

function setupFavAddClick() {
  $(".tba-fab-team").off("click");  // make sure only one click handler is attached at a time
  $(".tba-fab-team").click(function() {
    $(".tba-fab-team").off("click");
    $(this).find(".not-favorite").hide();
    addSpinner($(this));

    updateFavoriteTeams($(this).attr("data-team"), 'add', false);
  });
}

function setupFavDeleteClick() {
  $(".tba-fab-team").off("click");  // make sure only one click handler is attached at a time
  $(".tba-fab-team").click(function() {
    $(".tba-fab-team").off("click");
    $(this).find(".favorite").hide();
    addSpinner($(this));

    updateFavoriteTeams($(this).attr("data-team"), 'delete', false);
  });
}

function addSpinner(el) {
  el.append("<i class='fa fa-refresh fa-spin'></i>");
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
