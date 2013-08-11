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
    })
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
          $offset = $navbar_height;
        }
 
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top - $offset
        }, 250);
        event.preventDefault();
    });
	
	// Fancybox
	$(".fancybox").fancybox();

	// Disable browser autocompletes
	$('.search-query').attr('autocomplete', 'off');
	
//	// Typeahead for search
//  // Makes an AJAX call with the first character of the input.
//	var cachedsource = (function() {
//	  var datasource = {};
//    return function(query, process){
//      var first_letter = encodeURIComponent(query.charAt(0));
//      if ((first_letter == '') || (first_letter == ' ')) {
//    	  return [];
//    	}
//      if (datasource[first_letter] != null) {
//        return datasource[first_letter];
//      } else {
//        $.getJSON('/_/typeahead/' + first_letter, function(data) {
//          datasource[first_letter] = data;
//          process(datasource[first_letter]);
//        });
//      }
//    };
//	})();
//	
//	// helper function to match standard characters
//  function cleanUnicode(s){
//    var a = s.toLowerCase();
//    a = a.replace(/[àáâãäå]/g, "a");
//    a = a.replace(/æ/g, "ae");
//    a = a.replace(/ç/g, "c");
//    a = a.replace(/[èéêë]/g, "e");
//    a = a.replace(/[ìíîï]/g, "i");
//    a = a.replace(/ñ/g, "n");
//    a = a.replace(/[òóôõö]/g, "o");
//    a = a.replace(/œ/g, "oe");
//    a = a.replace(/[ùúûü]/g, "u");
//    a = a.replace(/[ýÿ]/g, "y");
//    return a;
//  };
//	
//	$('.search-query').typeahead({
//    source: cachedsource,
//    updater: function(label) {
//      var event_re = label.match(/(\d*)(.*)\[(.*?)\]/);
//      if (event_re != null) {
//        event_key = (event_re[1] + event_re[3]).toLowerCase();
//        url = "http://www.thebluealliance.com/event/" + event_key;
//        window.location.href = url;
//        return label;
//      }
//      var team_re = label.match(/(\d*) |.*/);
//      if (team_re != null) {
//        team_key = team_re[1];
//        url = "http://www.thebluealliance.com/team/" + team_key;
//        window.location.href = url;
//        return label;
//      }
//      return label;
//    },
//    matcher: function (item) {
//      return ~cleanUnicode(item).indexOf(cleanUnicode(this.query));
//    },
//    highlighter: function (item) {
//      var cleaned_item = cleanUnicode(item);
//      var query = this.query.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&');
//      var match_index = cleaned_item.search(new RegExp('(' + query + ')', 'ig'));
//      var match_len = query.length;
//      return item.substring(0, match_index) + '<strong>' +
//        item.substring(match_index, match_index + match_len) + '</strong>' +
//        item.substring(match_index + match_len);
//    }
//  });
	
	// Tooltips
	$("[rel=tooltip]").tooltip();
	
	// Fitvids
	$('.fitvids').fitVids();
});
