$(function() {
    // Setup redirect after login
    $('#mytba-login').click(function() {
      window.location.href = '/login?redirect=' + escape(document.URL.replace(document.location.origin, ""));
    });

    updateFavoritesList();  // Setup

    // Setup typeahead
    $('#add-favorite-team-input').attr('autocomplete', 'off');
    $('#add-favorite-team-input').typeahead([
      {
        prefetch: {
          url: '/_/typeahead/teams-all',
          filter: teamFilter
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
          url: '/_/account/favorites/add',
          data: data,
          success: function(data, textStatus, xhr) {
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
    url: '/_/account/favorites/1',
    success: function(favorites, textStatus, xhr) {
      for (var key in favorites) {
        insertFavoriteTeam(favorites[key]);
      }
      updateAllMatchbars();
      updateFavMatchOutline();
      updateAllTickerCards();
    },
    error: function(xhr, textStatus, errorThrown) {
      if (xhr.status == 401) {  // User not logged in
        var last_login_prompt = $.cookie("tba-gameday-last-login-prompt");
        var cur_epoch_ms = new Date().getTime();
        if (last_login_prompt == null || parseInt(last_login_prompt) + 1000*60*60*24 < cur_epoch_ms) {  // Show prompt at most once per day
          $('#login-modal').modal('show');
          $.cookie("tba-gameday-last-login-prompt", cur_epoch_ms);
        }
        // Not logged in. Change default behaviors.
        if (!isKickoff) {
          $('.mytba-button').attr('href', '#login-modal');
        }
        favoriteTeamsOff();
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
      url: '/_/account/favorites/delete',
      data: data,
      success: function(data, textStatus, xhr) {
        $("#favorite-" + teamNum).remove();
        updateAllMatchbars();
        updateFavMatchOutline();
        updateAllTickerCards();
      },
      error: function(xhr, textStatus, errorThrown) {
        $('#mytba-alert-container').append('<div class="alert alert-warning alert-dismissible" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button><strong>Oops! Failed to delete favorite.</strong><br>Something went wrong on our end. Please try again later.</div>');
      }
    });
  });
}

function getFavoriteTeamNums() {
  var favorites = $('.favorite-team');
  var favNums = [];
  for (var m=0; m<favorites.length; m++) {
    favNums.push(favorites[m].id.split('-')[1]);
  }
  return favNums;
}
