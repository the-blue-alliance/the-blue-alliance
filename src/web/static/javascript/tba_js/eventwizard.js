var ALLIANCE_PICKS_MAX = 3;
var NUM_ALLIANCES = 8;

ELIM_MAPPING = {
    1: [1, 1],  // (set, match)
    2: [2, 1],
    3: [3, 1],
    4: [4, 1],
    5: [1, 2],
    6: [2, 2],
    7: [3, 2],
    8: [4, 2],
    9: [1, 3],
    10: [2, 3],
    11: [3, 3],
    12: [4, 3],
    13: [1, 1],
    14: [2, 1],
    15: [1, 2],
    16: [2, 2],
    17: [1, 3],
    18: [2, 3],
    19: [1, 1],
    20: [1, 2],
    21: [1, 3]
};

OCTO_ELIM_MAPPING = {
    // octofinals
    1: [1, 1],  // (set, match)
    2: [2, 1],
    3: [3, 1],
    4: [4, 1],
    5: [5, 1],
    6: [6, 1],
    7: [7, 1],
    8: [8, 1],
    9: [1, 2],
    10: [2, 2],
    11: [3, 2],
    12: [4, 2],
    13: [5, 2],
    14: [6, 2],
    15: [7, 2],
    16: [8, 2],
    17: [1, 3],
    18: [2, 3],
    19: [3, 3],
    20: [4, 3],
    21: [5, 3],
    22: [6, 3],
    23: [7, 3],
    24: [8, 3],

    // quarterfinals
    25: [1, 1],
    26: [2, 1],
    27: [3, 1],
    28: [4, 1],
    29: [1, 2],
    30: [2, 2],
    31: [3, 2],
    32: [4, 2],
    33: [1, 3],
    34: [2, 3],
    35: [3, 3],
    36: [4, 3],

    // semifinals
    37: [1, 1],
    38: [2, 1],
    39: [1, 2],
    40: [2, 2],
    41: [1, 3],
    42: [2, 3],

    // finals
    43: [1, 1],
    44: [1, 2],
    45: [1, 3]
};

FIRST_MATCH = {
    "qf": 0,
    "sf": 12,
    "f": 18
};

OCTO_FIRST_MATCH = {
    "ef": 0,
    "qf": 24,
    "sf": 36,
    "f": 42
};

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
  'f': 5
};

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

function playoffTypeFromNumber(matchNum, is_octo){
    if (is_octo) {
        if (matchNum > 0 && matchNum <= 24) return "ef";
        if (matchNum > 24 && matchNum <= 36) return "qf";
        if (matchNum > 36 && matchNum <= 42) return "sf";
        return "f";
    } else {
        if (matchNum > 0 && matchNum <= 12) return "qf";
        if (matchNum > 12 && matchNum <= 18) return "sf";
        return "f";
    }
}

/* Returns one of {ef, qf, sf, f}
 * For use when some reports don't give the match number
 */
function playoffTypeFromMatchString(matchString){
    if(matchString.includes("Octofinal")) return "ef";
    if(matchString.includes("Quarterfinal")) return "qf";
    if(matchString.includes("Semifinal")) return "sf";
    if(matchString.includes("Final")) return "f";
    return null;
}

/* Return [type, set #, match #]
 * For use when some reports don't give the match number in the grid
 * ASSUMES 2016 label format, Quarter 1, Quarter 2, ..., Tiebreaker 1, Semi 1, ...
 */
function playoffTypeMatchAndSet(is_octo, match_string, last_type) {
    var set_num, match_num;
    var match_type = playoffTypeFromMatchString(match_string);
    if (match_type == null) {
        // We've found a "Tiebreaker X" match, assume type is the same as the previous
        match_type = last_type;
        set_num = parseInt(match_string.split(" ")[1]);
        match_num = 3;
        return [match_type, set_num, match_num];
    } else {
        var schedule_number = parseInt(match_string.split(" ")[1]);
        var overall_match_num = (is_octo ? OCTO_FIRST_MATCH[match_type] : FIRST_MATCH[match_type]) + schedule_number;
        var match_and_set = playoffMatchAndSet(overall_match_num, is_octo);
        return [match_type, match_and_set[0], match_and_set[1]]
    }
}

/* Return [set #, match #] */
function playoffMatchAndSet(totalMatchNum, is_octo){
    if (is_octo) {
        return OCTO_ELIM_MAPPING[totalMatchNum];
    } else {
        return ELIM_MAPPING[totalMatchNum];
    }
}

/* Load all valid events for this user */
var valid_events = [];
$.get( "/_/account/apiwrite_events", function(data) {
    var key_select = $("#event_key_select");
    var selected = key_select.val();
    valid_events.push('<option value="">Select Event</option>');
    $.each(JSON.parse(data), function(i, event) {
        valid_events.push('<option value="'+ event['value'] +'">'+ event['label'] +'</option>');
    });
    valid_events.push('<option value="other">Other</option>');
    key_select.html(valid_events.join('')).val(selected);
    if (selected != "other"){
        $('#auth_id').val("");
        $('#auth_secret').val("");
        $('#event_key').hide();
        $('#auth-tools').hide();
        $('#auth-container').hide();
    }}
);

if($('#event_key_select').val() != "other"){
    $('#event_key').hide();
}
$('#event_key_select').change(function(){
    var eventKey = $(this).val();
    $('#event_key').val(eventKey);
    if(eventKey == "other"){
        $('#event_key').val("").show();
        $('#auth-container').show();
        $('#auth-tools').show();
    }else{
        $('#event_key').hide();

        /* if the user is logged in, they don't need to manually input keys */
        $('#auth-container').hide();
        $('#auth-tools').hide();
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

$('#enable_fms_rankings').change(function(){
    update_fmsrankings_enabled();
});

function update_fmsrankings_enabled(){
    $('.update-rankings').each(function(){
        $(this).prop('disabled', !$('#enable_fms_rankings').is(':checked'));
    });
}

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
        trRed.append($('<td>', {rowspan: 2, 'style': 'border-top-width: 4px;border-right-width:4px;border-bottom-width:4px;width:17%'}).append($('<button>', {'class': 'update-rankings', text: 'Update Rankings','tabIndex':tabIndex+3})));
        $("#match-table").append(trRed);

        var trBlue = $('<tr>');
        for (j in match.alliances.blue.teams) {
          trBlue.append($('<td>', {'class': 'blue', 'data-matchKey-blueTeam': match.key, 'text': match.alliances.blue.teams[j].substring(3), 'style':'border-bottom-width:4px;'}));
        }
        trBlue.append($('<td>', {'style':'background-color: #9999FF;border-bottom-width:4px;'}).append($('<input>', {'id': match.key + '-blueScore', 'type': 'text', 'type': 'number', 'value': match.alliances.blue.score,'tabIndex':tabIndex+1}).css('max-width', '50px')));
        $("#match-table").append(trBlue);
        tabIndex = tabIndex+4;
      }

        update_fmsrankings_enabled();

    },
    error: function(data) {
      alert("Something went wrong! Please check your Event Key.");
    }
  });
});
