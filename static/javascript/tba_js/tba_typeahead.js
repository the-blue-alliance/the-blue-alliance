$(document).ready(function(){
  // Disable browser autocompletes
  $('.typeahead').attr('autocomplete', 'off');

  // Set up Twitter Typeahead
  $('.typeahead').typeahead([
    {
      name: 'teams',
      prefetch: {
        url: '/_/typeahead/teams-all',
        filter: teamFilter
      },
      header: '<div class="tba-typeahead-header">Teams</div>'
    },
    {
      name: 'events',
      prefetch: {
        url: '/_/typeahead/events-all',
        filter: eventFilter
      },
      header: '<div class="tba-typeahead-header">Events</div>'
    },
    {
      name: 'districts',
      prefetch: {
        url: '/_/typeahead/districts-all',
        filter: districtFilter
      },
      header: '<div class="tba-typeahead-header">Districts</div>'
    }
  ]);

  // Go to event and team pages on select or autocomplete
  function goToPage(obj, datum) {
    var event_re = datum.value.match(eventkeyRegex());
    if (event_re != null) {
      event_key = (event_re[1] + event_re[2]).toLowerCase();
      url = "/event/" + event_key;
      window.location.href = url;
    }
    var district_re = datum.value.match(/.+District \[(.+?)]/);
    if (district_re != null) {
      district_key = district_re[1];
      url = '/events/' + district_key.toLowerCase();
      window.location.href = url;
    }
    var team_re = datum.value.match(/(\d+) [|] .+/);
    if (team_re != null) {
      team_key = team_re[1];
      url = "/team/" + team_key;
      window.location.href = url;
    }
  }

  $('.typeahead').bind('typeahead:selected', goToPage);
  $('.typeahead').bind('typeahead:autocompleted', goToPage);

  // Submit form on Enter
  $(".typeahead").keypress(function (event) {
    if (event.which == 13) {
      this.form.submit();
    }
  });
});

// helper function to match standard characters
function cleanUnicode(s){
  var a = s.toLowerCase();
  a = a.replace(/[àáâãäå]/g, "a");
  a = a.replace(/æ/g, "ae");
  a = a.replace(/ç/g, "c");
  a = a.replace(/[èéêë]/g, "e");
  a = a.replace(/[ìíîï]/g, "i");
  a = a.replace(/ñ/g, "n");
  a = a.replace(/[òóôõö]/g, "o");
  a = a.replace(/œ/g, "oe");
  a = a.replace(/[ùúûü]/g, "u");
  a = a.replace(/[ýÿ]/g, "y");
  return a;
};

function teamFilter(data) {
  var to_return = [];
  for(var i=0; i<data.length; i++) {
    to_return.push({
      value: data[i],
      tokens: cleanUnicode(data[i]).split(' ')
    });
  }
  return to_return;
}

function eventkeyRegex() { return /(\d*).+\[(.+?)\]/; }

function eventFilter(data) {
  var to_return = [];
  for(var i=0; i<data.length; i++) {
    var event_re = cleanUnicode(data[i]).match(eventkeyRegex());
    var tokens = cleanUnicode(data[i]).replace('[', '').replace(']', '').split(' ');
    tokens.push((event_re[1] + event_re[2]));
    to_return.push({
      value: data[i],
      tokens: tokens
    });
  }
  return to_return;
}

function districtFilter(data) {
  var to_return = [];
  for(var i=0; i<data.length; i++) {
    to_return.push({
      value: data[i],
      tokens: cleanUnicode(data[i]).replace('[', '').replace(']', '').split(' ')
    });
  }
  return to_return;
}
