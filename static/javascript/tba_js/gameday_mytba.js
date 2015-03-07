var urlBase = '';

$(function() {
    updateFavoritesList();  // Setup

    // Form for adding favorites
    $('#add-favorite-team-form').on('submit', function(e) {
        e.preventDefault();
        var data = $("#add-favorite-team-form :input").serializeArray();
        $.ajax({
          type: 'POST',
          dataType: 'json',
          url: urlBase + '/_/account/favorites',
          data: data,
          success: function(msg) {
            updateFavoritesList();
          },
          error: function(xhr, textStatus, errorThrown) {
            console.log("FAIL: " + xhr.status);
          }
        });
    });
});

// For getting favorites from server
function updateFavoritesList() {
  $.ajax({
    type: 'GET',
    dataType: 'json',
    url: urlBase + '/_/account/favorites',
    success: function(favorites) {
      for (var key in favorites) {
        if (favorites[key]['model_type'] == 1) {  // Only show favorite teams
          insertFavoriteTeam(favorites[key]);
        }
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      console.log("FAIL: " + xhr.status);
    }
  });
}

function insertFavoriteTeam(favorite_team) {
  var team_number = favorite_team['model_key'].substring(3);
  var existing_favorites = $("#favorite-teams")[0].children;

  // Insert team sorted by team number. Don't re-add if the team is already listed.
  var added = false;
  var element = $("<li id=favorite-" + team_number + " class='favorite-team'>" + team_number + " <a data-team-number='" + team_number + "' class='remove-favorite' title='Remove'><span class='glyphicon glyphicon-remove'></span></a></li>");
  for (var i=0; i<existing_favorites.length; i++) {
    var existing_team_number = parseInt(existing_favorites[i].id.replace(/[A-Za-z$-]/g, ""));
    if (existing_team_number > team_number) {
      element.insertBefore($("#" + existing_favorites[i].id));
      added = true;
      break;
    } else if (existing_team_number == team_number) {
      added = true;
      break;
    }
  }
  if (!added) {
    $("#favorite-teams").append(element);
  }

  // Attach deletion callback
  $(".remove-favorite").click(function() {
    var teamNum = $(this).attr("data-team-number");
    var data = {
      'action': 'delete',
      'model_type': 1,
      'model_key': 'frc' + teamNum
    };
    $.ajax({
      type: 'POST',
      dataType: 'json',
      url: urlBase + '/_/account/favorites',
      data: data,
      success: function(msg) {
        $("#favorite-" + teamNum).remove();
      },
      error: function(xhr, textStatus, errorThrown) {
        console.log("FAIL: " + xhr.status);
      }
    });
  });
}
