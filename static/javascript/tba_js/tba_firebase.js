var lastMatchesRef = new Firebase('https://thebluealliance.firebaseio.com/last_matches');
var lastMatchesQuery = lastMatchesRef.limit(10);

lastMatchesQuery.on('child_added', function(snapshot) {
  var match = snapshot.val();
  updateFeedbar(match);
});
