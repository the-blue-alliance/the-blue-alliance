function getFavoriteTeams() {
  var cookieName = "tba-favorite-teams";
  var storedFavoriteTeams = $.cookie(cookieName);

  console.log(storedFavoriteTeams);

  if (storedFavoriteTeams == null) {
    // Set cookie expiration
    var date = new Date();
    date.setTime(date.getTime() + (5 * 60 * 1000));  // 5 minutes

    $.ajax({
      type: 'GET',
      dataType: 'json',
      url: '/_/account/favorites/1',
      success: function(favorites, textStatus, xhr) {
        var favoriteTeams = {};
        for (var key in favorites) {
          favoriteTeams[favorites[key]['model_key']] = true;
        }
        $.cookie(cookieName, JSON.stringify(favoriteTeams), { expires: date });

        updateFavorites(favoriteTeams);
      },
      error: function(xhr, textStatus, errorThrown) {
        $.cookie(cookieName, JSON.stringify({}), { expires: date });
      }
    });
  } else {
    updateFavorites(JSON.parse(storedFavoriteTeams));
  }
}

function updateFavorites(favoriteTeams) {
  updateMatchFavorites(favoriteTeams);
  updateTeamlistFavorites(favoriteTeams);
  updateTeamFABFavorites(favoriteTeams);
}

function updateMatchFavorites(favoriteTeams) {
  $(".favorite-team-dot").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();  // Dot
      $(this).closest('tr').find('.favorite-match-icon').show();  // Star
    }
  });
}

function updateTeamlistFavorites(favoriteTeams) {
  $(".favorite-team-icon").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();
    }
  });
}

function updateTeamFABFavorites(favoriteTeams) {
  $(".tba-fab-team").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).find(".favorite").show();
      $(this).find(".not-favorite").hide();
    }
  });
}

$(document).ready(function(){
  getFavoriteTeams();
});
