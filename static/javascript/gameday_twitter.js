$(document).ready(function() {
  var TWITTER_HTML = $('#twitter-widget').html();
  renderTwitterWidget();
  
  $(window).resize(function(){
    renderTwitterWidget();
  });
  
  // Modified version of the basic JS Twitter provides in order to handle dynamic resizing.
  function renderTwitterWidget() {
    $('#twitter-widget').html(TWITTER_HTML);
    var height = $('#twitter-widget').css('height');
    $('.twitter-timeline').attr('height', height);
    $('#twitter-wjs').remove();
    !function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];
      js=d.createElement(s);
      js.id=id;
      js.src="//platform.twitter.com/widgets.js";
      fjs.parentNode.insertBefore(js,fjs);
    }(document,"script","twitter-wjs");
  }
});
