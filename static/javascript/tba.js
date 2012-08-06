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

	//Disable browser autocompletes
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
			    	itemSelected: selectResult
			    });
			});
		};
	});
});