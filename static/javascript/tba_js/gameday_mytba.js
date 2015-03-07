var urlBase = 'https://tbatv-prod-hrd.appspot.com';  // Use https

$(function() {
    // Setup redirect after login
    $('#mytba-login').click(function() {
      window.location.href = '/account?redirect=' + escape(document.URL);
    });

    updateFavoritesList();  // Setup

    // Setup typeahead
    $('#add-favorite-team-input').attr('autocomplete', 'off');
    $('#add-favorite-team-input').typeahead([
      {
        prefetch: {
          url: '/_/typeahead/teams-all',
          filter: unicodeFilter
        },
      }
    ]);
    // Submit form when entry chosen
    function doAction(obj, datum) {
      var team_re = datum.value.match(/(\d+) [|] .+/);
      if (team_re != null) {
        team_key = 'frc' + team_re[1];
        $('#add-favorite-team-model-key').attr('value', team_key);
        $('#add-favorite-team-form').submit();
      }
    }
    $('#add-favorite-team-input').bind('typeahead:selected', doAction);
    $('#add-favorite-team-input').bind('typeahead:autocompleted', doAction);

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
            $('#add-favorite-team-input').typeahead('setQuery', '');
          },
          error: function(xhr, textStatus, errorThrown) {
            $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to add favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
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
      updateAllMatchbars();
    },
    error: function(xhr, textStatus, errorThrown) {
      if (xhr.status == 401) {
        $('#login-modal').modal('show');
        $('#settings-button').attr('href', '#login-modal');
      }
      $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Unable to get favorites.</strong><br>Something went wrong on our end. Please try again later.</div>');
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
        updateAllMatchbars();
      },
      error: function(xhr, textStatus, errorThrown) {
        $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to delete favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
      }
    });
  });
}
