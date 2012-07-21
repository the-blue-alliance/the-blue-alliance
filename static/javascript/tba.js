window.onscroll = scrollheader;

function scrollheader() {
    var scrollx = document.body.scrollLeft
    var header = document.getElementById('topHeader')
    header.style.left = 0-scrollx+'px'
}

function selectResult(item, val, text) {
	window.location.href = ("http://www.thebluealliance.com" + val);

}

$(function() {
	// Fancybox
	$(".fancybox").fancybox();
	
	// Typeahead for search
	// Currently does a one-time JSON get that returns
	// the entire list of teams and events.
	// Can be optimized.
	$.getJSON('/_/typeahead', function(data) {
		$('.search-query').typeahead({
			// Used for when we implement a better typeahead solution
	    	/*ajax: {
		    	    url: '/typeahead',
		    	    method: 'get',
		    	    triggerLength: 3,
		    },*/
			source: data,
	    	itemSelected: selectResult
	    });
	});	
});