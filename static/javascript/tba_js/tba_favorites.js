var favoriteTeamsCookieName = "tba-favorite-teams2";

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
          $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to add favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
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
          $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to add favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
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
          setLocalFavoriteTeams({});
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
  date.setTime(date.getTime() + (5 * 60 * 1000));  // Set 5 minutes cookie expiration
  // $.cookie(favoriteTeamsCookieName, JSON.stringify(favoriteTeams), { expires: date });
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
  updateTeamFABFavoriteTeams(favoriteTeams);
}

function updateMatchFavoriteTeams(favoriteTeams) {
  // Reset all stars
  $(".favorite-match-icon").each(function() {
    $(this).hide();
  });

  $(".favorite-team-dot").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();  // Dot
      $(this).closest('tr').find('.favorite-match-icon').show();  // Star
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
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).find(".favorite").show();
      $(this).find(".not-favorite").hide();
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
    console.log("CLICK ADD");
    console.log($(this).attr("data-team"));
    updateFavoriteTeams($(this).attr("data-team"), 'add')
  });
}

function setupFavDeleteClick() {
  $(".tba-fab-team").off("click");  // make sure only one click handler is attached at a time
  $(".tba-fab-team").click(function() {
    $(".tba-fab-team").off("click");
    console.log("CLICK DELETE");
    console.log($(this).attr("data-team"));
    updateFavoriteTeams($(this).attr("data-team"), 'delete')
  });
}

$(document).ready(function(){
  console.log(getLocalFavoriteTeams());
  setupFavAddClick();
  updateFavoriteTeams();
});
