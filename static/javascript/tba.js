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

function selectTypeaheadResult(item, val, text) {
	if (!isNaN(val)) {
		url = "http://www.thebluealliance.com/team/" + val;
	} else {
		url = "http://www.thebluealliance.com/event/" + val;
	}
	window.location.href = url;
}

// General JS for all pages
$(function() {
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
	
	// Typeahead for search
	// Currently does a one-time JSON get that returns
	// the entire list of teams and events.
	// Can be optimized.
	$('.search-query').focus(function() {
		if (!$('.search-query').data('typeahead')) {
			$.getJSON('/_/typeahead', function(data) {
				$('.search-query').typeahead({
					// Used for when we implement a better typeahead solution
			    	/*ajax: {
				    	    url: '/_/typeahead',
				    	    method: 'get',
				    	    triggerLength: 3,
				    },*/
					source: data,
			    	itemSelected: selectTypeaheadResult
			    });
			});
		};
	});
	
	// Tooltips
	$("[rel=tooltip]").tooltip();
	
	// Charts
	var chartsData = $(".xcharts-line-data-1");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html())
		data = []
		for (var key in raw) {
			var value = raw[key]
			data = data.concat([{"x": parseInt(key), "y": value}])
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "bar",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": data}],
						 }
		var opts = {"tickFormatY": function(y){ return y + "%"; },}
		var myChart = new xChart('bar', chartData, '#' + chartId + '-chart', opts);
	}
	
	var chartsData = $(".xcharts-line-data-2");
	for (var i=0; i < chartsData.length; i++) {
		var chartId = chartsData[i].id;
		var raw = JSON.parse($('#' + chartId).html())
		data = []
		for (var key in raw) {
			var tuple = raw[key]
			data = data.concat([{"x": tuple[0], "y": tuple[1]}])
		}
		var chartData = {"xScale": "ordinal",
						 "yScale": "linear",
						 "type": "line-dotted",
						 "main": [{"className": "." + chartId + '-elements',
							 	   "data": data}],
						 }
		var myChart = new xChart('line', chartData, '#' + chartId + '-chart');
	}
});

// Kickoff Countdown
update_kickoff_countdown();
function update_kickoff_countdown() {
	var kickoff_utc = new Date(Date.UTC(2013,0,5,14,0,0));
	var current_utc = new Date().getTime();
	var time_diff = kickoff_utc - current_utc;
	var seconds = Math.floor(time_diff / 1000);
	var minutes = Math.floor(seconds / 60);
	var hours = Math.floor(minutes / 60);
	var days = Math.floor(hours / 24);
	var content;

	hours %= 24;
    minutes %= 60;
    seconds %= 60;
    
    if (time_diff < 0) {
        $('.kickoff-countdown').remove();
    }

    $('.kickoff-countdown-days').text(days);
    $('.kickoff-countdown-hours').text(hours);
    $('.kickoff-countdown-minutes').text(minutes);
    $('.kickoff-countdown-seconds').text(seconds);
    setTimeout('update_kickoff_countdown()', 1000);
}
