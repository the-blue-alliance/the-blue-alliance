function makeRequest(request_path, request_body, feedback) {
  var auth_id = $('#auth_id').val();
  var auth_secret = $('#auth_secret').val();
  var auth_sig = CryptoJS.MD5(auth_secret + request_path + request_body).toString();

  $.ajax({
    type: 'POST',
    url: request_path,
    dataType: 'json',
    contentType: 'application/json',
    headers: {
      'X-TBA-Auth-Id': auth_id,
      'X-TBA-Auth-Sig': auth_sig
    },
    data: request_body,
    success: function(data) {
      feedback.css('background-color', '#419641');
    },
    error: function(data) {
      feedback.css('background-color', '#c12e2a');
      alert(data.responseText);
    }
  });
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

function playoffTypeFromNumber(matchNum){
    if(matchNum > 0 && matchNum <= 8) return "qf";
    if(matchNum > 8 && matchNum <= 14) return "sf";
    return "f";
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

    var auth = JSON.parse(getCookie(eventKey+"_auth"));
    if(!auth){
        alert("No auth found");
        return false;
    }
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

$('#schedule_preview').hide();
$('#schedule-ok').hide();
$('#schedule_file').change(function(){
    var f = this.files[0];
    var reader = new FileReader();
    var name = f.name;
    reader.onload = function(e) {
        var data = e.target.result;
        var workbook = XLSX.read(data, {type: 'binary'});
        var first_sheet = workbook.SheetNames[0];
        var sheet = workbook.Sheets[first_sheet];

        //parse the excel to array of matches
        //headers start on 5th row
        var matches = XLSX.utils.sheet_to_json(sheet, {range:4});

        if(matches.length > 0){
            $('#schedule_preview_status').html("Loaded "+matches.length+" matches");
        }else{
            $('#schedule_preview_status').html("No matches found in the file.");
            return;
        }

        var request_body = [];

        $('#schedule_preview').empty();
        for(var i=0; i<matches.length; i++){
            var match = matches[i];

            // check for invalid match
            if(!match['Match']){
                continue;
            }

            var row = $('<tr>');
            row.append($('<td>').html(match['Time']));
            row.append($('<td>').html(match['Description']));
            row.append($('<td>').html(match['Match']));
            row.append($('<td>').html(match['Blue 1']));
            row.append($('<td>').html(match['Blue 2']));
            row.append($('<td>').html(match['Blue 3']));
            row.append($('<td>').html(match['Red 1']));
            row.append($('<td>').html(match['Red 2']));
            row.append($('<td>').html(match['Red 3']));

            $('#schedule_preview').append(row);

            var compLevel, setNumber, matchNumber;
            // only works for 2015 format
            matchNumber = parseInt(match['Match']);
            setNumber = 1;
            if(match['Description'].indexOf("Qualification") == 0){
                compLevel = "qm";
            }else{
                compLevel = playoffTypeFromNumber(matchNumber);
            }

            // make json dict
            request_body.push({
                'comp_level': compLevel,
                'set_number': setNumber,
                'match_number': matchNumber,
                'alliances': {
                    'red': {
                    'teams': ['frc'+match['Red 1'], 'frc'+match['Red 2'], 'frc'+match['Red 3']],
                    'score': null
                    },'blue': {
                    'teams': ['frc'+match['Blue 1'], 'frc'+match['Blue 2'], 'frc'+match['Blue 3']],
                    'score': null
                    }
                },
                'time_string': match['Time'],
            });
        }

        $('#schedule_preview').show();
        $('#schedule-ok').show();
        $('#schedule-ok').click(function(){
            $(this).css('background-color', '#eb9316');
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/matches/update', JSON.stringify(request_body), $(this));
        });

    };

    $('#schedule_preview_status').html("Loading...");
    reader.readAsBinaryString(f);
});

$('#setup-ok').click(function(e) {
  e.preventDefault();

  $.ajax({
    url: '/api/v2/event/' + $('#event_key').val() + '/matches',
    dataType: 'json',
    headers: {'X-TBA-App-Id': 'tba-web:match-input:v01'},
    success: function(matches) {
      $("#match-table").empty();

      for (i in matches) {
        var match = matches[i];
        match.play_order = COMP_LEVELS_PLAY_ORDER[match.comp_level] * 1000000 + match.match_number * 1000 + match.set_number
      }
      matches.sort(function(a, b) { return a.play_order - b.play_order});

      for (i in matches) {
        var match = matches[i];

        var trRed = $('<tr>');
        trRed.append($('<td>', {rowspan: 2, text: match.key.split('_')[1]}));
        for (j in match.alliances.red.teams) {
          trRed.append($('<td>', {class: 'red', 'data-matchKey-redTeam': match.key, text: match.alliances.red.teams[j].substring(3)}));
        }
        trRed.append($('<td>', {class: 'redScore'}).append($('<input>', {id: match.key + '-redScore', type: 'text', type: 'number', value: match.alliances.red.score}).css('max-width', '50px')));
        trRed.append($('<td>', {rowspan: 2}).append($('<button>', {class: 'update-match', 'data-matchKey': match.key, 'data-matchCompLevel': match.comp_level, 'data-matchSetNumber': match.set_number, 'data-matchNumber': match.match_number, text: 'SUBMIT'})));
        $("#match-table").append(trRed);

        var trBlue = $('<tr>');
        for (j in match.alliances.blue.teams) {
          trBlue.append($('<td>', {class: 'blue', 'data-matchKey-blueTeam': match.key, text: match.alliances.blue.teams[j].substring(3)}));
        }
        trBlue.append($('<td>', {class: 'blueScore'}).append($('<input>', {id: match.key + '-blueScore', type: 'text', type: 'number', value: match.alliances.blue.score}).css('max-width', '50px')));
        $("#match-table").append(trBlue);
      }

      $('.update-match').click(function(e) {
        e.preventDefault();

        $(this).parent().css('background-color', '#eb9316');

        var matchKey = $(this).attr('data-matchKey');
        var redEls = $("[data-matchKey-redTeam='" + matchKey + "']");
        var blueEls = $("[data-matchKey-blueTeam='" + matchKey + "']");
        var redTeams = [];
        var blueTeams = [];
        for (var i=0; i<redEls.length; i++) {
          redTeams.push('frc' + redEls[i].textContent);
        }
        for (var i=0; i<blueEls.length; i++) {
          blueTeams.push('frc' + blueEls[i].textContent);
        }
        var redScore = parseInt($('#' + matchKey + '-redScore')[0].value);
        var blueScore = parseInt($('#' + matchKey + '-blueScore')[0].value);

        var match = {
          'comp_level': $(this).attr('data-matchCompLevel'),
          'set_number': parseInt($(this).attr('data-matchSetNumber')),
          'match_number': parseInt($(this).attr('data-matchNumber')),
          'alliances': {
            'red': {
              'teams': redTeams,
              'score': redScore
            },
            'blue': {
              'teams': blueTeams,
              'score': blueScore
            }
          },
        };
        var request_body = JSON.stringify([match]);
        makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/matches/update', request_body, $(this).parent());
      });
    },
    error: function(data) {
      alert("Something went wrong! Please check your Event Key.");
    }
  });
});


