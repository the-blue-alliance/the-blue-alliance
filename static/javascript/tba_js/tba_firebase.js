var lastMatchesRef = new Firebase('https://thebluealliance.firebaseio.com/last_matches');
var lastMatchesQuery = lastMatchesRef.limit(10);

$(document).ready(function(){
  
});


lastMatchesQuery.on('child_added', function(snapshot) {
  var key = snapshot.name();
  var message = snapshot.val();
  console.log(message);
});
