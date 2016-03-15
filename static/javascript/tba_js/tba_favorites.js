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

        updateMatchFavorites(favoriteTeams);
      },
      error: function(xhr, textStatus, errorThrown) {
        $.cookie(cookieName, JSON.stringify({}), { expires: date });
      }
    });
  } else {
    updateMatchFavorites(JSON.parse(storedFavoriteTeams));
  }
}

function updateMatchFavorites(favoriteTeams) {
  $(".favorite-match-icon").each(function () {
    var match_teams = JSON.parse($(this).attr("data-teams"));
    for (var i in match_teams) {
      if (match_teams[i] in favoriteTeams) {
        $(this).show();
      }
    }
  });
}

$(document).ready(function(){
  getFavoriteTeams();
});
