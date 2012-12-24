function updateFeedbar(match) {
  var comp_level = match.comp_level.toUpperCase()
  comp_level = comp_level == 'QM' ? 'Q' : comp_level;
  var match_number = (comp_level == 'QF' || comp_level == 'SF' || comp_level == 'F') ? match.set_number + '-' + match.match_number : match.match_number;
  
  var match_label = getEventKey(match).substring(4).toUpperCase() + ' ' + comp_level + match_number;
  var red_win = match.winning_alliance == 'red' ? 'win' : '';
  var blue_win = match.winning_alliance == 'blue' ? 'win' : '';
  
  var red_teams = match.alliances.red.teams[0].substring(3) + ', ' +
    match.alliances.red.teams[1].substring(3) + ', ' +
    match.alliances.red.teams[2].substring(3)
  var blue_teams = match.alliances.blue.teams[0].substring(3) + ', ' +
    match.alliances.blue.teams[1].substring(3) + ', ' +
    match.alliances.blue.teams[2].substring(3)
  
  var red_score = match.alliances.red.score;
    var blue_score = match.alliances.blue.score;

  var new_match = '<div class="scores">' +
    '<div class="match-number">' + match_label + '</div>' +
    '<div class="red ' + red_win + '">' + red_teams + ' - ' + red_score + '</div>' +
    '<div class="blue ' + blue_win + '">' + blue_teams + ' - ' + blue_score + '</div>' +
    '<div class="div_helper"></div></div>';
  $('.feed_bar').prepend(new_match);
}

function getEventKey(match) {
  return match.key_name.split('_')[0];
}
