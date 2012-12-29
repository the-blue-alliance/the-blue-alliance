var finish_utc;
$(document).ready(function(){
  var finish_utc_args = JSON.parse($('#countdown-finish-time').html());
  finish_utc = new Date(Date.UTC(finish_utc_args[0],
                                 finish_utc_args[1],
                                 finish_utc_args[2],
                                 finish_utc_args[3],
                                 finish_utc_args[4],
                                 finish_utc_args[5]));
  update_countdown();
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
  }

  $('.countdown-days').text(days);
  $('.countdown-hours').text(hours);
  $('.countdown-minutes').text(minutes);
  $('.countdown-seconds').text(seconds);
  setTimeout('update_countdown()', 1000);
}
