function updateMatchbar(snapshot) {
  var event_key = snapshot.name();
  var event_data = snapshot.val();
  var upcoming_matches = event_data.upcoming_matches;
  var last_matches = event_data.last_matches;

  // Render upcoming matches
  if (upcoming_matches != null) {
    for (var i=0; i<upcoming_matches.length; i++) {
      var upcoming_match = renderMatch(upcoming_matches[i]).addClass('upcoming_match');
      $('.' + event_key + '_matches').append(upcoming_match);
    }
  }
  
  // Render last played match
  if (last_matches != null) {
    var winning_alliance = (last_matches[0].winning_alliance == '') ? 'tie' : last_matches[0].winning_alliance;
    var last_match = renderMatch(last_matches[0]).addClass('finished_match_' + winning_alliance);
    $('.' + event_key + '_matches').prepend(last_match);
  }
  
  /*
 
  $('.feed_bar').prepend(new_match);
  $('.scores').click(function(){
    $(".scores").fancybox({
      'overlayColor'  : '#333',
      'overlayShow'   : true,
      'autoDimensions': false,
      'width'         : 0.9*$(".video_container").width(),
      'height'        : 0.9*$(".video_container").height(),
      'type'          : 'iframe',
      'href'          : '/event/' + getEventKey(match)
    });
  });
  new_match.focus();
  new_match.removeClass('new_scores');
  */
}

function renderMatch(match) {
  var comp_level = match.comp_level.toUpperCase()
  comp_level = (comp_level == 'QM') ? 'Q' : comp_level;
  var match_number = (comp_level == 'QF' || comp_level == 'SF' || comp_level == 'F') ? match.set_number + '-' + match.match_number : match.match_number;
  var match_label = comp_level + match_number;
  
  var red_teams = match.alliances.red.teams[0].substring(3) + ', ' +
    match.alliances.red.teams[1].substring(3) + ', ' +
    match.alliances.red.teams[2].substring(3)
  var blue_teams = match.alliances.blue.teams[0].substring(3) + ', ' +
    match.alliances.blue.teams[1].substring(3) + ', ' +
    match.alliances.blue.teams[2].substring(3)
  
  var red_score = match.alliances.red.score;
  var blue_score = match.alliances.blue.score;
  red_score = (red_score == -1) ? '' : ' - ' + red_score;
  blue_score = (blue_score == -1) ? '' : ' - ' + blue_score;

  var match_number = $('<div>', {'class': 'match-number', text: match_label});
  var red_score = $('<div>', {'class': 'red', text: red_teams + red_score});
  var blue_score = $('<div>', {'class': 'blue' , text: blue_teams + blue_score});
  var alliances = $('<div>', {'class': 'alliances'});
  alliances.append(red_score).append(blue_score);
  
  var new_match = $('<div>', {'class': 'match', 'id': match.key_name}).append(match_number).append(alliances);
  return new_match;
}
