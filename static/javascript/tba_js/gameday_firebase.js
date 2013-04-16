var eventsRef = new Firebase('https://thebluealliance-dev.firebaseio.com/events');
var eventsQuery = eventsRef.limit(10);

eventsQuery.on('child_changed', function(snapshot) {
	updateMatchbar(snapshot)
});

eventsQuery.on('child_added', function(snapshot) {
	updateMatchbar(snapshot);
});
