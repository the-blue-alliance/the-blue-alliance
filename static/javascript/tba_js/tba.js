// facebook login
window.fbAsyncInit = function() {
FB.init({
  appId      : '434443279939497', // App ID
  channelUrl : '//www.thebluealliance.com/channel', // Channel File
  status     : true, // check login status
  cookie     : true, // enable cookies to allow the server to access the session
  xfbml      : true  // parse XFBML
});

// Additional initialization code here
// listen for and handle auth.statusChange events
FB.Event.subscribe('auth.statusChange', function(response) {
  if (response.authResponse) {
    // user has auth'd your app and is logged into Facebook
    FB.api('/me', function(me){
      if (me.name) {
        $('#auth-displayname').html(me.name);
      }
    });
    $('#auth-loggedout').hide();
    $('#auth-loggedin').show();
  } else {
    // user has not auth'd your app, or is not logged into Facebook
    $('#auth-loggedout').show();
    $('#auth-loggedin').hide();
  }
});

// respond to clicks on the login and logout links
$('#auth-loginlink').click(function(){
  FB.login();
});
$('#auth-logoutlink').click(function(){
  FB.logout();
});
};

// Load the SDK Asynchronously
(function(d){
	var js, id = 'facebook-jssdk', ref = d.getElementsByTagName('script')[0];
	if (d.getElementById(id)) {return;}
	js = d.createElement('script'); js.id = id; js.async = true;
	js.src = "//connect.facebook.net/en_US/all.js";
	ref.parentNode.insertBefore(js, ref);
}(document));

// General JS for all pages
$(document).ready(function(){
	// Jumping to page section
  $('.smooth-scroll').bind('click',function(event){
    var $anchor = $(this);
    var $navbar_position = $('.navbar').css('top');
    var $navbar_height = parseInt($('.navbar').css('height'));
    var $offset = 0;
    
    // Takes care of changing navbar size/position due to @media width
    if ($navbar_position == '0px') {
      $offset = $navbar_height + 10;
    }
    
    var target_offset = $($anchor.attr('href')).offset();
    if (target_offset == null) {
      var pixels = 0;
    } else {
      var pixels = target_offset.top - $offset;
    }
  
    $('html, body').stop().animate({
        scrollTop: pixels
    }, 250);
    event.preventDefault();
  });
	
	// Fancybox
	$(".fancybox").fancybox();
	
	// Tooltips
	$("[rel=tooltip]").tooltip();
	
	// Fitvids
	$('.fitvids').fitVids();

  $('#preferences input:radio').addClass('input_hidden');
  $('#preferences label').click(function() {
      $(this).addClass('selected').siblings().removeClass('selected');
  });
});
