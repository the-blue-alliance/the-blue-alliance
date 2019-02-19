var finish_utc;
$(document).ready(function(){
	if ($('#countdown-finish-time').length != 0) {
	  var utc_iso8601 = $('#countdown-finish-time').html();
	  finish_utc = new Date(utc_iso8601);
	  update_countdown();
	}
});

function update_countdown() {
  var current_utc = new Date().getTime();
  var time_diff = finish_utc - current_utc;
  var seconds = Math.floor(time_diff / 1000);
  var minutes = Math.floor(seconds / 60);
  var hours = Math.floor(minutes / 60);
  var days = Math.floor(hours / 24);
  var content;

  hours %= 24;
  minutes %= 60;
  seconds %= 60;
  
  if (time_diff < 0) {
      $('.countdown').remove();
      return;
  }

  $('.countdown-days').text(days);
  $('.countdown-hours').text(hours);
  $('.countdown-minutes').text(minutes);
  $('.countdown-seconds').text(seconds);
  setTimeout('update_countdown()', 1000);
}
