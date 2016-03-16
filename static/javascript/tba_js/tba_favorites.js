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
  $(".favorite-team-dot").each(function() {
    if ($(this).attr("data-team") in favoriteTeams) {
      $(this).show();  // Dot
      $(this).closest('tr').find('.favorite-match-icon').show();  // Star
    }
  });
}

$(document).ready(function(){
  getFavoriteTeams();
});
