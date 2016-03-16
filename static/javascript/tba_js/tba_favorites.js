var favoriteTeamsCookieName = "tba-favorite-teams";

function updateFavoriteTeams() {
  updateFavoriteTeams(null, null);
}

function updateFavoriteTeams(teamKey, action) {
  /*
  Updates Favorites locally and on the server and
  updates the page to reflect these changes
  teamKey: like "frc254" or null
  action: "add" or "delete" or null (doesn't do anything if teamKey is null)
  */
  var storedFavoriteTeams = getLocalFavoriteTeams();

  if (teamKey != null) {
    if (action == 'add') {
      console.log("REMOTE ADD");
      $.ajax({
        type: 'POST',
        url: '/_/account/favorites/add',
        data: {'model_key': teamKey, 'model_type': 1},
        success: function(data, textStatus, xhr) {
          addLocalFavoriteTeam(teamKey);
          updateFavoriteTeams();
        },
        error: function(xhr, textStatus, errorThrown) {
          if (xhr.status == 401) {
            $('#login-modal').modal('show');
          } else {
            $('#fixed-alert-container').append('<div class="alert alert-danger alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to add favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
          }
          updateFavoriteTeams();
        }
      });
    } else if (action == 'delete') {
      console.log("REMOTE DELETE");
      $.ajax({
        type: 'POST',
        url: '/_/account/favorites/delete',
        data: {'model_key': teamKey, 'model_type': 1},
        success: function(data, textStatus, xhr) {
          deleteLocalFavoriteTeam(teamKey);
          updateFavoriteTeams();
        },
        error: function(xhr, textStatus, errorThrown) {
          if (xhr.status == 401) {
            $('#login-modal').modal('show');
          } else {
            $('#fixed-alert-container').append('<div class="alert alert-danger alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to delete favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
          }
          updateFavoriteTeams();
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
          updatePageFavoriteTeams(favoriteTeams);
        },
        error: function(xhr, textStatus, errorThrown) {
          setLocalFavoriteTeams(null);
          updatePageFavoriteTeams({});
        }
      });
    } else {
      updatePageFavoriteTeams(storedFavoriteTeams);
    }
  }
}

function getLocalFavoriteTeams() {
  return JSON.parse($.cookie(favoriteTeamsCookieName));
}

function setLocalFavoriteTeams(favoriteTeams) {
  var date = new Date();
  date.setTime(date.getTime() + (1 * 60 * 1000));  // Set 5 minutes cookie expiration
  $.cookie(favoriteTeamsCookieName, JSON.stringify(favoriteTeams), { expires: date });
}

function addLocalFavoriteTeam(teamKey) {
  var storedFavoriteTeams = getLocalFavoriteTeams();
  if (storedFavoriteTeams != null) {
    console.log("Adding: " + teamKey);
    storedFavoriteTeams[teamKey] = true;
    setLocalFavoriteTeams(storedFavoriteTeams);
    console.log(storedFavoriteTeams);
  }
}

function deleteLocalFavoriteTeam(teamKey) {
  var storedFavoriteTeams = getLocalFavoriteTeams();
  if (storedFavoriteTeams != null && teamKey in storedFavoriteTeams) {
    console.log("Deleting: " + teamKey);
    delete storedFavoriteTeams[teamKey];
    setLocalFavoriteTeams(storedFavoriteTeams);
    console.log(storedFavoriteTeams);
  }
}

function updatePageFavoriteTeams(favoriteTeams) {
  updateMatchFavoriteTeams(favoriteTeams);
  updateTeamlistFavoriteTeams(favoriteTeams);
  setTimeout(function() {updateTeamFABFavoriteTeams(favoriteTeams)}, 3000);
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

    console.log("CLICK ADD");
    console.log($(this).attr("data-team"));
    updateFavoriteTeams($(this).attr("data-team"), 'add')
  });
}

function setupFavDeleteClick() {
  $(".tba-fab-team").off("click");  // make sure only one click handler is attached at a time
  $(".tba-fab-team").click(function() {
    $(".tba-fab-team").off("click");
    $(this).find(".favorite").hide();
    addSpinner($(this));

    console.log("CLICK DELETE");
    console.log($(this).attr("data-team"));
    updateFavoriteTeams($(this).attr("data-team"), 'delete')
  });
}

function addSpinner(el) {
  el.append("<i class='fa fa-refresh fa-spin'/>");
  el.prop("disabled", true);
}

$(document).ready(function(){
  // Setup redirect after login
  $('#mytba-login').click(function() {
    window.location.href = '/account?redirect=' + escape(document.URL.replace(document.location.origin, ""));
  });

  console.log(getLocalFavoriteTeams());
  setupFavAddClick();
  updateFavoriteTeams();
});
