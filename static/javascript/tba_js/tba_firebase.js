var myDataRef = new Firebase('https://thebluealliance.firebaseio.com/matches');

$(document).ready(function(){
  
});


myDataRef.on('child_added', function(snapshot) {
  var key = snapshot.name();
  var message = snapshot.val();
  console.log(key);
  console.log(message);
});
