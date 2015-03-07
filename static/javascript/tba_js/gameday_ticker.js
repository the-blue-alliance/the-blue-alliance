var firebase = new Firebase('https://thebluealliance.firebaseio.com/notifications/');
var pageSize = 25;
var numToAnimate = 3; // How many cards to animate
var earliestKey = null;
var visibleTypes = {'favorite_teams_only': true};  // default = visible

$(window).load(function() {
    $('#ticker-filter').click(function() {
        $('#ticker-filter-options').slideToggle();
    });

    firebase.limitToLast(pageSize).on('child_added', function(childSnapshot) {
        var card = buildNotificationCard(childSnapshot.val());
        $('#ticker-notifications').prepend(card);
        updateVisibility(card, card.attr('data-type'));

        if (earliestKey == null || childSnapshot.key() < earliestKey) {
            earliestKey = childSnapshot.key();
        }
    });

    // Show/hide notification types based on checkboxes
    $('input[type="checkbox"]').click(function(){
        var type = $(this).attr("value");
        if (type in visibleTypes) {
            visibleTypes[type] = !visibleTypes[type];
        } else {
            visibleTypes[type] = false;
        }
        updateAllVisibility();
    });
});

function updateAllVisibility() {
    var favTeamNums = getFavoriteTeamNums();
    var index = 0;
    $('#ticker-notifications').children().each(function () {
        var dataType = $(this).attr('data-type');
        if (!(dataType in visibleTypes) || visibleTypes[dataType]) {
            if (visibleTypes['favorite_teams_only'] && (dataType == 'upcoming_match' || dataType == 'match_score')) {
                var isFav = false;
                for (var i=0; i<favTeamNums.length; i++) {
                    if ($(this).attr('data-team-nums').split(',').indexOf(favTeamNums[i]) != -1) {
                        isFav = true;
                        break;
                    }
                }
                if (!isFav) {
                    if (index < 3) {
                        $(this).slideUp();
                    } else {
                        $(this).hide();
                    }
                    return;
                }
            }
            if (index < 3) {
                $(this).slideDown();
            } else {
                $(this).show();
            }
        } else {
            if (index < 3) {
                $(this).slideUp();
            } else {
                $(this).hide();
            }
            return;
        }
        if ($(this).is(':visible')) {
            index++;
        }
    });
}

function updateVisibility(e, type) {
    // New cads are always hidden. This chooses whether or not to show it
    if (!(type in visibleTypes) || visibleTypes[type]) {
        if (type == 'match_score' || type == 'upcoming_match') {
            var favTeamNums = getFavoriteTeamNums();
            for (var i=0; i<favTeamNums.length; i++) {
                if (e.attr('data-team-nums').split(',').indexOf(favTeamNums[i]) != -1) {
                    e.slideDown();
                }
            }
        } else {
            e.slideDown();
        }
    }
}

function loadMore() {
    if (earliestKey != null) {
        firebase.orderByKey().endAt(earliestKey).limitToLast(pageSize).once('value', function(snapshot) {
            var data = snapshot.val();
            var cards = [];
            for (childKey in data) {
                var card = buildNotificationCard(data[childKey]);
                cards.push(card);

                if (earliestKey == null || childKey < earliestKey) {
                    earliestKey = childKey;
                }
            }

            cards.reverse();
            for (idx in cards.slice(1)) {// First element is repeated
                var card = cards[idx];
                $('#ticker-notifications').append(card);
                updateVisibility(card, card.attr('data-type'));
            }
        });
    }
}

// Load more notifications when scroll reaches the bottom
$('.ticker_panel').scroll(function() {
    if ($(this).scrollTop() + $(this).innerHeight()>=$(this)[0].scrollHeight) {
        loadMore();
    }
});

function buildNotificationCard(data){
    var payload = data['payload'];
    if(payload == null){
        return;
    }
    var timeString = data['time'];
    var timeFormatted = new Date(timeString+"+00:00").toLocaleString();
    var messageData = JSON.stringify(payload['message_data'], null, 2);
    var messageType = payload['message_type'];

    var card = $('<div>', {'class': 'panel'});
    card.hide();  // default with cards hidden
    card.attr('data-type', messageType);
    var body = $('<div>', {'class': 'panel-body'});
    var eventKey = 'XXXX????';
    switch(messageType) {
        case 'alliance_selection':
            card.addClass('panel-material-red');
            eventKey = payload['message_data']['event_key'];

            body.append($('<strong>', {text: 'Alliance Selection Results: TODO'}));
            break;
        case 'awards_posted':
            card.addClass('panel-material-green');
            eventKey = payload['message_data']['event_key'];

            body.append($('<strong>', {text: 'Awards Posted'}));
            break;
        case 'match_score':
            card.addClass('panel-material-indigo');
            eventKey = payload['message_data']['match']['event_key'];

            body.append($('<strong>', {text: 'Match Result: ' + matchKeyToReadableName(payload['message_data']['match']['key'])}));

            var redTeams = payload['message_data']['match']['alliances']['red']['teams'];
            var blueTeams = payload['message_data']['match']['alliances']['blue']['teams'];
            var redScore = payload['message_data']['match']['alliances']['red']['score'];
            var blueScore = payload['message_data']['match']['alliances']['blue']['score'];
            body.append(constructMatchTable(redTeams, blueTeams, redScore, blueScore));
            card.attr('data-team-nums', redTeams.concat(blueTeams));
            break;
        case 'schedule_updated':
            card.addClass('panel-material-light-blue');
            eventKey = payload['message_data']['event_key'];

            body.append($('<strong>').append($('<a>', {'href': 'http://www.thebluealliance.com/event/'+eventKey, 'target': '_blank', text: 'Schedule Updated'})));
            break;
        case 'starting_comp_level':
            card.addClass('panel-material-purple');
            eventKey = payload['message_data']['event_key'];

            levels = {
                'qm': 'Qualification',
                'qf': 'Quarterfinal',
                'sf': 'Semifinal',
                'f': 'Final',
            }

            body.append($('<strong>', {text: levels[payload['message_data']['comp_level']] + ' matches starting'}));
            break;
        case 'upcoming_match':
            card.addClass('panel-material-orange');
            eventKey = payload['message_data']['match_key'].split('_')[0];

            body.append($('<strong>', {text: 'Upcoming Match: ' + matchKeyToReadableName(payload['message_data']['match_key'])}));

            var redTeams = payload['message_data']['team_keys'].slice(0, 3);
            var blueTeams = payload['message_data']['team_keys'].slice(3, 6);
            body.append(constructMatchTable(redTeams, blueTeams, null, null));
            card.attr('data-team-nums', redTeams.concat(blueTeams));
            break;
        default:
            body.append($('<strong>', {text: messageType}));
            body.append($('<pre>', {text: messageData}));
            break;
    }
    var eventName = payload['message_data']['event_name'];
    // Strip things out like "FIM District - " This is crude and may break
    var splitEventName = eventName.split(' - ');
    if (splitEventName.length == 1) {
        eventName = splitEventName[0];
    } else {
        eventName = splitEventName[1];
    }
    var heading = $('<div>', {
        'class': 'panel-heading',
        html: "<a href='http://thebluealliance.com/event/"+eventKey+"' target='_blank' style='color:#FFFFFF'>"+eventName+" ["+eventKey.toUpperCase().substring(4)+"]</a>"
    });

    var footer = $('<div>', {'class': 'panel-footer'});
    var time = $('<div>', {'class': 'pull-right'});
    time.append($('<small>', {text: timeFormatted}));
    footer.append(time)
    return card.append(heading).append(body).append(footer);
}

function constructMatchTable(redTeams, blueTeams, redScore, blueScore) {
    for (var i=0; i<redTeams.length; i++) {
        redTeams[i] = redTeams[i].substring(3);
    }
    for (var i=0; i<blueTeams.length; i++) {
        blueTeams[i] = blueTeams[i].substring(3);
    }

    var favTeamNums = getFavoriteTeamNums();
    var matchTable = $('<table>', {'class': 'match-table'});

    var redRow = $('<tr>');
    for (var i in redTeams) {
        var td = $('<td>', {'class': 'red'}).append($('<a>', {'href': '/team/'+redTeams[i], 'target': '_blank', text: redTeams[i]}));
        if (favTeamNums.indexOf(redTeams[i]) != -1) {
            td.addClass('red-favorite');
        }
        redRow.append(td)
    }
    if (redScore != null) {
        redRow.append($('<td>', {'class': 'redScore', text: redScore}));
    }
    var blueRow = $('<tr>');
    for (var i in blueTeams) {
        var td = $('<td>', {'class': 'blue'}).append($('<a>', {'href': '/team/'+blueTeams[i], 'target': '_blank', text: blueTeams[i]}));
        if (favTeamNums.indexOf(blueTeams[i]) != -1) {
            td.addClass('blue-favorite');
        }
        blueRow.append(td)
    }
    if (blueScore != null) {
        blueRow.append($('<td>', {'class': 'blueScore', text: blueScore}));
    }

    var tbody = $('<tbody>');
    tbody.append(redRow);
    tbody.append(blueRow);
    matchTable.append(tbody)
    return matchTable
}

function matchKeyToReadableName(matchKey) {
    return matchKey.split('_')[1];
}
