window.onscroll = scrollheader;

function scrollheader() {
    var scrollx = document.body.scrollLeft
    var header = document.getElementById('topHeader')
    header.style.left = 0-scrollx+'px'
}

function selectTypeaheadResult(item, val, text) {
	if (!isNaN(val)) {
		url = "http://www.thebluealliance.com/team/" + val;
	} else {
		url = "http://www.thebluealliance.com/event/" + val;
	}
	window.location.href = url;
}

$(function() {
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
