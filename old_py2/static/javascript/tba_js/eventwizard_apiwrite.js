/* Utility functions to write to the trusted API */

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

function getYoutubeId(url) {
    // regex from http://stackoverflow.com/a/9102270
    var regex = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    var match = url.match(regex);
    if (match && match[2].length == 11) {
        return match[2];
    } else {
        return null;
    }
}

function cleanTeamNum(number) {
    return number.toString().trim().replace("*", "")
}

$('#teams-ok').click(function(){
    if(!$("#team_list").val()){
        alert("Please enter team data.");
        return true;
    }

    var teams = $('#team_list').val().split("\n");
    for(var i=0; i<teams.length; i++){
        var teamNum = parseInt(teams[i]);
        if(!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999){
            alert("Invalid team "+teams[i]);
            return true;
        }
        teams[i] = "frc"+teamNum;
    }
    $(this).css('background-color', '#eb9316');
    makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/team_list/update', JSON.stringify(teams), $(this));
});

$('#alliances-ok').click(function(){
    var request = [];
    var count = 0;
    for(var count=1; count <= NUM_ALLIANCES; count++){
        var alliance = [];
        var captain = $("#alliance"+count+"-captain").val();
        var pick1 = $("#alliance"+count+"-pick1").val();
        var pick2 = $("#alliance"+count+"-pick2").val();
        var pick3 = $("#alliance"+count+"-pick3").val();

        if(captain){
            alliance.push('frc'+captain);
        }else{
            request.push([]);
            continue;
        }
        if(pick1) alliance.push('frc'+pick1);
        if(pick2) alliance.push('frc'+pick2);
        if(pick3) alliance.push('frc'+pick3);

        request.push(alliance);
    }
    $(this).css('background-color', '#eb9316');
    makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/alliance_selections/update', JSON.stringify(request), $(this));
});

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
        var request_body = [];

        $('#schedule_preview').empty();
        $('#schedule_preview').html("<tr><th>Time</th><th>Description</th><th>Match</th><th>TBA Key</th><th>Blue 1</th><th>Blue 2</th><th>Blue 3</th><th>Red 1</th><th>Red 2</th><th>Red 3</th></tr>");
        var filter = $('input[name="import-comp-level"]:checked').val();
        for(var i=0; i<matches.length; i++){
            var match = matches[i];

            // check for invalid match
            if(!match['Description'] || !match['Red 1']){
                continue;
            }

            var compLevel, setNumber, matchNumber, rawMatchNumber, matchKey;
            var has_octo = $('input[name="alliance-count-schedule"]:checked').val() == "16";
            if (match['Match']) {
                rawMatchNumber = parseInt(match['Match']);
            } else if (match['Description'].indexOf('#') >= 0) {
                rawMatchNumber = parseInt(match['Description'].split('#')[1]);
            } else {
                rawMatchNumber = parseInt(match['Description'].split(' ')[1]);
            }
            if(!match.hasOwnProperty('Description') || match['Description'].indexOf("Qualification") == 0){
                matchNumber = parseInt(match['Description'].split(' ')[1]);
                compLevel = "qm";
                setNumber = 1;
                matchKey = "qm" + matchNumber;
            }else{
                compLevel = playoffTypeFromNumber(rawMatchNumber, has_octo);
                var setAndMatch = playoffMatchAndSet(rawMatchNumber, has_octo);
                setNumber = setAndMatch[0];
                matchNumber = setAndMatch[1];
                matchKey = compLevel + setNumber + "m" + matchNumber;
            }

            /* Ignore matches the user doesn't want */
            if(filter != "all" && filter != compLevel){
                continue;
            }

            var row = $('<tr>');
            row.append($('<td>').html(match['Time']));
            row.append($('<td>').html(match['Description']));
            row.append($('<td>').html(rawMatchNumber));
            row.append($('<td>').html($('#event_key').val() + "_" + matchKey));
            row.append($('<td>').html(cleanTeamNum(match['Blue 1'])));
            row.append($('<td>').html(cleanTeamNum(match['Blue 2'])));
            row.append($('<td>').html(cleanTeamNum(match['Blue 3'])));
            row.append($('<td>').html(cleanTeamNum(match['Red 1'])));
            row.append($('<td>').html(cleanTeamNum(match['Red 2'])));
            row.append($('<td>').html(cleanTeamNum(match['Red 3'])));

            $('#schedule_preview').append(row);

            // make json dict
            request_body.push({
                'comp_level': compLevel,
                'set_number': setNumber,
                'match_number': matchNumber,
                'alliances': {
                    'red': {
                    'teams': ['frc'+cleanTeamNum(match['Red 1']), 'frc'+cleanTeamNum(match['Red 2']), 'frc'+cleanTeamNum(match['Red 3'])],
                    'score': null
                    },'blue': {
                    'teams': ['frc'+cleanTeamNum(match['Blue 1']), 'frc'+cleanTeamNum(match['Blue 2']), 'frc'+cleanTeamNum(match['Blue 3'])],
                    'score': null
                    }
                },
                'time_string': match['Time'],
            });
        }


         if(request_body.length > 0){
            $('#schedule_preview_status').html("Loaded "+request_body.length+" matches");
        }else{
            $('#schedule_preview_status').html("No matches found in the file.");
            return;
        }


        $('#schedule_preview').show();
        $('#schedule-ok').show();
        $('#schedule-ok').unbind('click').click(function(){
            $(this).css('background-color', '#eb9316');
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/matches/update', JSON.stringify(request_body), $(this));
        });

    };

    $('#schedule_preview_status').html("Loading...");
    reader.readAsBinaryString(f);
});

$('#results_file').change(function(){
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
        var matches = XLSX.utils.sheet_to_json(sheet, {range:2});

        var request_body = [];

        $('#results_preview').empty();
        $('#results_preview').html("<tr><th>Time</th><th>Match</th><th>TBA Key</th><th>Red 1</th><th>Red 2</th><th>Red 3</th><th>Blue 1</th><th>Blue 2</th><th>Blue 3</th><th>Red Score</th><th>Blue Score</th></tr>");
        var good_matches = 0;
        var last_match_type = null;
        for(var i=0; i<matches.length; i++){
            var match = matches[i];

            // check for invalid match
            if(!match['Time']){
                continue;
            }
            good_matches++;

            var compLevel, setNumber, matchNumber;
            var matchKey;
            var has_octo = $('input[name="alliance-count-results"]:checked').val() == "16";
            if (match['Match'].includes("Qualification")) {
                matchNumber = parseInt(match['Match'].split(" ")[1]);
                compLevel = "qm";
                setNumber = 1;
                matchKey = "qm" + matchNumber;
            } else {
                var levelSetAndMatch = playoffTypeMatchAndSet(has_octo, match['Match'], last_match_type);
                compLevel = levelSetAndMatch[0];
                setNumber = levelSetAndMatch[1];
                matchNumber = levelSetAndMatch[2];
                matchKey = compLevel + setNumber + "m" + matchNumber;
            }
            last_match_type = compLevel;

            var row = $('<tr>');
            row.append($('<td>').html(match['Time']));
            row.append($('<td>').html(match['Match']));
            row.append($('<td>').html($('#event_key').val() + "_" + matchKey));
            row.append($('<td>').html(cleanTeamNum(match['Red 1'])));
            row.append($('<td>').html(cleanTeamNum(match['Red 2'])));
            row.append($('<td>').html(cleanTeamNum(match['Red 3'])));
            row.append($('<td>').html(cleanTeamNum(match['Blue 1'])));
            row.append($('<td>').html(cleanTeamNum(match['Blue 2'])));
            row.append($('<td>').html(cleanTeamNum(match['Blue 3'])));
            row.append($('<td>').html(match['Red Score']));
            row.append($('<td>').html(match['Blue Score']));

            $('#results_preview').append(row);

            // make json dict
            request_body.push({
                'comp_level': compLevel,
                'set_number': setNumber,
                'match_number': matchNumber,
                'alliances': {
                    'red': {
                    'teams': ['frc'+cleanTeamNum(match['Red 1']), 'frc'+cleanTeamNum(match['Red 2']), 'frc'+cleanTeamNum(match['Red 3'])],
                    'score': parseInt(match['Red Score'])
                    },'blue': {
                    'teams': ['frc'+cleanTeamNum(match['Blue 1']), 'frc'+cleanTeamNum(match['Blue 2']), 'frc'+cleanTeamNum(match['Blue 3'])],
                    'score': parseInt(match['Blue Score'])
                    }
                },
                'time_string': match['Time'],
            });
        }

        if(request_body.length > 0){
            $('#results_preview_status').html("Loaded "+request_body.length+" matches");
        }else{
            $('#results_preview_status').html("No matches found in the file.");
            return;
        }


        $('#results_preview').show();
        $('#results-ok').show();
        $('#results-ok').unbind('click').click(function(){
            $(this).css('background-color', '#eb9316');
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/matches/update', JSON.stringify(request_body), $(this));
        });

    };

    $('#schedule_preview_status').html("Loading...");
    reader.readAsBinaryString(f);
});

$('#rankings_file').change(function(){
    var f = this.files[0];
    var reader = new FileReader();
    var name = f.name;
    reader.onload = function(e) {
        var data = e.target.result;
        var workbook = XLSX.read(data, {type: 'binary'});
        var first_sheet = workbook.SheetNames[0];
        var sheet = workbook.Sheets[first_sheet];

        //parse the excel to array of matches
        var rankings = XLSX.utils.sheet_to_json(sheet, {range:4});

        var request_body = {};

        // 2015 Headers
        //var headers = ['Rank', 'Team', 'Qual Avg', 'Coopertition', 'Auto', 'Container', 'Tote', 'Litter', 'DQ', 'Played'];

        // 2016 Headers
        //var headers  = ['Rank', 'Team', 'RS', 'Auto', 'S/C', 'Boulders', 'Defenses', 'W-L-T', 'Played', 'DQ'];
        //var display_headers = ["Rank", "Team", "Ranking Score", "Auto", "Scale/Challenge", "Goals", "Defense", "Record (W-L-T)", "Played", 'DQ'];
        //var is_int = [true, true, true, true, true, false, true, true];

        // 2017 Headers
        //var headers = ['Rank', 'Team', 'RS', 'TotalPts', 'Auto', 'Rotor', 'Takeoff', 'kPa', 'W-L-T', 'DQ', 'Played'];
        //var display_headers = ['Rank', 'Team', 'Ranking Score', 'Match Points', 'Auto', 'Rotor', 'Takeoff', 'kPa', 'Record (W-L-T)', 'DQ', 'Played'];
        //var is_num = [true, true, true, true, true, true, false, true, true];

        // 2018 Headers
        //var headers = ['Rank', 'Team', 'RS', 'Endgame', 'Auto', 'Ownership', 'Vault', 'W-L-T', 'DQ', 'Played'];
        //var display_headers = ['Rank', 'Team', 'Ranking Score', 'End Game', 'Auto', 'Ownership', 'Vault', 'Record (W-L-T)', 'DQ', 'Played'];
        //var is_num = [true, true, true, true, true, false, true, true];

        // 2019 Headers
        var headers = ['Rank', 'Team', 'RS', 'Cargo Pts', 'Panel Pts', 'HAB Pts', 'Sandstorm', 'W-L-T', 'DQ', 'Played'];
        var display_headers = ['Rank', 'Team', 'Ranking Score', 'Cargo', 'Hatch Panel', 'HAB Climb', 'Sandstorm Bonus', 'Record (W-L-T)', 'DQ', 'Played'];
        var is_num = [true, true, true, true, true, false, true, true];

        $('#rankings_preview').empty();
        $('#rankings_preview').html("<tr><th>" + display_headers.join("</th><th>") + "</th></tr>");

        request_body['breakdowns'] = display_headers.slice(2, 8);
        request_body['rankings'] = [];

        for(var i=0; i<rankings.length; i++){
            var rank = rankings[i];

            // check for invalid row
            if(!rank['Rank'] || isNaN(rank['Rank'])){
                continue;
            }

            var row = $('<tr>');
            for(var j=0; j<headers.length; j++){
                row.append($('<td>').html(rank[headers[j]]));
            }

            $('#rankings_preview').append(row);

            var breakdown = {};
            breakdown['team_key'] = 'frc'+rank['Team'];
            breakdown['rank'] = parseInt(rank['Rank']);
            breakdown['played'] = parseInt(rank['Played']);
            breakdown['dqs'] = parseInt(rank['DQ']);
            for(var j=0; j<request_body['breakdowns'].length; j++){
                var val = rank[headers[j + 2]];
                breakdown[request_body['breakdowns'][j]] = is_num[j] ? Number(val.toString().replace(',','')) : val;
            }
            request_body['rankings'].push(breakdown);
        }

        if(request_body['rankings'].length > 0){
            $('#rankings_preview_status').html("Loaded rankings for "+request_body['rankings'].length+" teams");
        }else{
            $('#rankings_preview_status').html("No rankings found in the file.");
            return;
        }

        $('#rankings_preview').show();
        $('#rankings-ok').show();
        $('#rankings-ok').unbind('click').click(function(){
            $(this).css('background-color', '#eb9316');
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/rankings/update', JSON.stringify(request_body), $(this));
        });

    };

    $('#schedule_preview_status').html("Loading...");
    reader.readAsBinaryString(f);
});

$('#teams_file').change(function(){
    var f = this.files[0];
    var reader = new FileReader();
    var name = f.name;
    reader.onload = function(e) {
        var data = e.target.result;
        var workbook = XLSX.read(data, {type: 'binary'});
        var first_sheet = workbook.SheetNames[0];
        var sheet = workbook.Sheets[first_sheet];

        //parse the excel to array of matches
        //headers start on 2nd row
        var teams = XLSX.utils.sheet_to_json(sheet, {range:2});

        var request_body = {};

        $('#teams_preview').empty();
        $('#teams_preview').html("<tr><th>Team Number</th><th>Team Name</th></tr>");

        var request_body = []
        for(var i=0; i<teams.length; i++){
            var team = teams[i];

            // check for invalid row
            if(!team['#']){
                continue;
            }

            var teamNum = parseInt(team['#']);
            if(!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999){
                alert("Invalid team "+teams[i]);
                return true;
            }
            request_body[i] = "frc"+teamNum;

            var row = $('<tr>');
            row.append($('<td>').html(teamNum));
            row.append($('<td>').html(team['Short Name']));

            $('#teams_preview').append(row);

        }

        if(request_body.length > 0){
            $('#teams_preview_status').html("Loaded "+request_body.length+" teams");
        }else{
            $('#teams_preview_status').html("No teams found in the file.");
            return;
        }


        $('#teams_preview').show();
        $('#fmsteams-ok').show();
        $('#fmsteams-ok').unbind('click').click(function(){
            $(this).css('background-color', '#eb9316');
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/team_list/update', JSON.stringify(request_body), $(this));
        });

    };

    $('#schedule_preview_status').html("Loading...");
    reader.readAsBinaryString(f);
});

$('#match-table').on('click', 'button', function(e) {
    if($(this).attr('class') == "update-rankings") {
        updateRankings($(this));
    }else if($(this).attr('class') == "update-match") {
        updateMatchScore($(this), e);
    }
});

function updateMatchScore(cell, e) {
    e.preventDefault();

    cell.parent().css('background-color', '#eb9316');

    var matchKey = cell.attr('data-matchKey');
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
        'comp_level': cell.attr('data-matchCompLevel'),
        'set_number': parseInt(cell.attr('data-matchSetNumber')),
        'match_number': parseInt(cell.attr('data-matchNumber')),
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
    makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/matches/update', request_body, cell.parent());

    var video_request = {};
    var yt_url = $("#"+matchKey+"_video").val();
    var video_key = getYoutubeId(yt_url);
    if (!video_key) {
        return;
    }
    video_request[matchKey.split('_')[1]] = video_key;
    makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/match_videos/add', JSON.stringify(video_request), $("#"+matchKey+"_video").parent());
}

function updateRankings(cell) {
    cell.parent().css('background-color', '#eb9316');
    $.ajax({
        type: 'GET',
        url: 'http://10.0.100.5/Pit/GetData?random=' + Math.random(),
        dataType: 'json',
        cache: false,
        timeout: 5000,
        success: function (data) {
            console.log(data);

            var request_body = {};

            // 2015 Headers
            //var breakdowns = ['Avg', 'CP', 'AP', 'RC', 'TP', 'LP'];

            // 2016 Headers
            //var breakdowns  = ['RS', 'Sort2', 'Sort3', 'Sort4', 'Sort 5', 'Wins', 'Losses', 'Ties', 'Played', 'DQ'];
            //var display = ["Ranking Score", "Auto", "Scale/Challenge", "Goals", "Defense", "Wins", "Losses", "Ties", "Played", 'DQ'];

            // 2017 Headers
            var breakdowns  = ['RS', 'Sort2', 'Sort3', 'Sort4', 'Sort 5', 'Wins', 'Losses', 'Ties', 'Played', 'DQ'];
            var display = ["Ranking Score", "Auto", "Scale/Challenge", "Goals", "Defense", "Wins", "Losses", "Ties", "Played", 'DQ'];

            var rankData = data['Ranks'];
            request_body['breakdowns'] = display;
            request_body['rankings'] = [];
            for(var i=0; i<rankData.length; i++){
                // Turn team number -> team key
                rankData[i]['Team'] = "frc"+rankData[i]['Team'];
                var teamRank = {};
                teamRank['team_key'] = rankData[i]['Team'];
                teamRank['rank'] = rankData[i]['Rank'];
                teamRank['played'] = rankData[i]['Played'];
                teamRank['dqs'] = 0;
                for(var j=0; j<breakdowns.length; j++){
                    teamRank[display[j]] = Number(rankData[i][breakdowns[j]].toString().replace(',',''));
                }
                request_body['rankings'].push(teamRank);
            }
            makeRequest('/api/trusted/v1/event/' + $('#event_key').val() + '/rankings/update', JSON.stringify(request_body), cell.parent());
        },
        error: function (error) {
            console.log(error);
            // We had an error getting the results so set the top of the screen red
            alert("Error getting rankings. Are you sure you're connected to the field network?");
            cell.parent().css({ 'background-color': '#c12e2a' });
        }
    });
}
