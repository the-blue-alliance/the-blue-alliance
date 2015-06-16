var ALLIANCE_PICKS_MAX = 3;
var NUM_ALLIANCES = 8;
function generateAllianceTable(size, table){
    for(var i=size; i>0; i--){
        var row = $('<tr>');
        row.append($('<td>').html("Alliance "+i));
        row.append($('<td>', {'class': 'captain'}).append($('<input>', {'id': "alliance"+i+"-captain", 'placeholder': "Captain "+i})));
        for(var j=1; j<=ALLIANCE_PICKS_MAX; j++){
            row.append($('<td>', {'class':"pick-"+j}).append($('<input>', {'class':"pick-"+j, 'id': "alliance"+i+"-pick"+j, 'placeholder': "Pick "+i+"-"+j})));
        }
        table.after(row);
    }
}

var COMP_LEVELS_PLAY_ORDER = {
  'qm': 1,
  'ef': 2,
  'qf': 3,
  'sf': 4,
  'f': 5,
}

function setCookie(name, value) {
    document.cookie = name + "=" + value;
}

function getCookie(name) {
    var name = name + "=";
    var allCookies = document.cookie.split(';');
    for(var i=0; i<allCookies.length; i++) {
        var c = allCookies[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}

/* ONLY FOR 2015 */
function playoffTypeFromNumber(matchNum){
    if(matchNum > 0 && matchNum <= 8) return "qf";
    if(matchNum > 8 && matchNum <= 14) return "sf";
    return "f";
}

function playoffTypeFromMatchString(matchString){
    if(matchString.indexOf("Quarterfinal") == 0) return "qf";
    if(matchString.indexOf("Semifinal") == 0) return "sf";
    if(matchString.indexOf("Final") == 0) return "f";
}

/* ONLY FOR 2015 */
function playoffMatchNumber(type, totalMatchNum){
    if(type == "sf") return totalMatchNum - 8;
    if(type == "f") return totalMatchNum - 14;
    return totalMatchNum;
}

if($('#event_key_select').val() != "other"){
    $('#event_key').hide();
}
$('#event_key_select').change(function(){
    var eventKey = $(this).val();
    $('#event_key').val(eventKey);
    if(eventKey == "other"){
        $('#event_key').val("").show()
    }else{
        $('#event_key').hide();
    }

    // clear auth boxes
    $('#auth_id').val("");
    $('#auth_secret').val("");
});

$('#load_auth').click(function(){
    var eventKey = $('#event_key').val();
    if(!eventKey){
        alert("You must select an event.");
        return false;
    }
    var cookie = getCookie(eventKey+"_auth");
    if(!cookie){
        alert("No auth found");
        return false;
    }
    var auth = JSON.parse(cookie);
    $('#auth_id').val(auth['id']);
    $('#auth_secret').val(auth['secret']);
});

$('#store_auth').click(function(){
    var eventKey = $('#event_key').val();
    var authId = $('#auth_id').val();
    var authSecret = $('#auth_secret').val();

    if(!eventKey){
        alert("You must select an event.");
        return false;
    }

    if(!authId || !authSecret){
        alert("You must enter your auth id and secret.");
        return false;
    }

    var auth = {};
    auth['id'] = authId;
    auth['secret'] = authSecret;

    setCookie(eventKey+"_auth", JSON.stringify(auth));

    alert("Auth stored!");
});

generateAllianceTable(8, $('#alliances tr:last'));
$('.pick-3').hide();
$('input[name="alliance-size"]:radio').change(function(){
    var size = $(this).val();
    if(size == "2"){
        $('.pick-2').val("").hide();
        $('.pick-3').val("").hide();
    }else if(size == "3"){
        $('.pick-2').show();
        $('.pick-3').val("").hide();
    }else if(size == "4"){
        $('.pick-2').show();
        $('.pick-3').show();
    }
});

$('#auth-help').hide();
$('#show-help').click(function(){
    $('#auth-help').attr("display", "inline").show();
});

$('#teams_preview').hide();
$('#fmsteams-ok').hide();

$('#schedule_preview').hide();
$('#schedule-ok').hide();

$('#results_preview').hide();
$('#results-ok').hide();

$('#rankings_preview').hide();
$('#rankings-ok').hide();

$('#fetch-matches').click(function(e) {
  e.preventDefault();
  $('#match_play_load_status').html("Loading matches");
  $.ajax({
    url: '/api/v2/event/' + $('#event_key').val() + '/matches',
    dataType: 'json',
    headers: {'X-TBA-App-Id': 'tba-web:match-input:v01'},
    success: function(matches) {
      $("#match-table").empty();
      $('#match_play_load_status').html("Loaded "+matches.length+" matches");
      var tabIndex = 1;
      for (i in matches) {
        var match = matches[i];
        match.play_order = COMP_LEVELS_PLAY_ORDER[match.comp_level] * 1000000 + match.match_number * 1000 + match.set_number
      }
      matches.sort(function(a, b) { return a.play_order - b.play_order});

      for (i in matches) {
        var match = matches[i];

        var trRed = $('<tr>');
        trRed.append($('<td>', {rowspan: 2, text: match.key.split('_')[1], 'style': 'border-top-width: 4px;border-left-width:4px;border-bottom-width:4px;'}));
        for (j in match.alliances.red.teams) {
          trRed.append($('<td>', {'class': 'red', 'data-matchKey-redTeam': match.key, 'text': match.alliances.red.teams[j].substring(3), 'style':'border-top-width:4px;'}));
        }
        trRed.append($('<td>', {'style':'background-color: #FF9999;border-top-width:4px;'}).append($('<input>', {'id': match.key + '-redScore', 'type': 'text', 'type': 'number', 'value': match.alliances.red.score, 'tabIndex':tabIndex}).css('max-width', '50px')));
        trRed.append($('<td>', {rowspan: 2, 'style': 'border-top-width: 4px;border-right-width:4px;border-bottom-width:4px;width:17%'}).append($('<input>', {'id': match.key+"_video", 'placeholder': 'YouTube URL'})));
        trRed.append($('<td>', {rowspan: 2, 'style': 'border-top-width: 4px;border-right-width:4px;border-bottom-width:4px;width:17%'}).append($('<button>', {'class': 'update-match', 'data-matchKey': match.key, 'data-matchCompLevel': match.comp_level, 'data-matchSetNumber': match.set_number, 'data-matchNumber': match.match_number, text: 'SUBMIT - '+match.key.split('_')[1],'tabIndex':tabIndex+2})));
        $("#match-table").append(trRed);

        var trBlue = $('<tr>');
        for (j in match.alliances.blue.teams) {
          trBlue.append($('<td>', {'class': 'blue', 'data-matchKey-blueTeam': match.key, 'text': match.alliances.blue.teams[j].substring(3), 'style':'border-bottom-width:4px;'}));
        }
        trBlue.append($('<td>', {'style':'background-color: #9999FF;border-bottom-width:4px;'}).append($('<input>', {'id': match.key + '-blueScore', 'type': 'text', 'type': 'number', 'value': match.alliances.blue.score,'tabIndex':tabIndex+1}).css('max-width', '50px')));
        $("#match-table").append(trBlue);
        tabIndex = tabIndex+3;
      }

    },
    error: function(data) {
      alert("Something went wrong! Please check your Event Key.");
    }
  });
});
