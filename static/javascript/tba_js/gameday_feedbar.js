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

  var match_number = $('<div>', {'class': 'match-number', text: match_label});
  var red_score = $('<div>', {'class': 'red ' + red_win, text: red_teams + ' - ' + red_score});
  var blue_score = $('<div>', {'class': 'blue ' + blue_win, text: blue_teams + ' - ' + blue_score});
  var div_helper = $('<div>', {'class': 'div_helper'});
  
  var new_match = $('<div>', {'class': 'scores new'}).append(match_number).append(red_score).append(blue_score).append(div_helper);
  $('.feed_bar').prepend(new_match);
  $('.scores').click(function(){
    $(".scores").fancybox({
      'overlayColor'  : '#333',
      'overlayShow' : true,
      'autoDimensions': false,
      'width'     :   0.9*$(".video_container").width(),
      'height'    : 0.9*$(".video_container").height(),
      'type'      : 'iframe',
      'href'      : '/event/' + getEventKey(match)
    });
  });
  new_match.focus();
  new_match.removeClass('new');
}

function getEventKey(match) {
  return match.key_name.split('_')[0];
}
