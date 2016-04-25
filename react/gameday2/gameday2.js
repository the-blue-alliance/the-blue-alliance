import React from 'react';
import GamedayFrame from './components/GamedayFrame';
var ReactDOM = require('react-dom');

// [{'webcasts': [{u'channel': u'6540154', u'type': u'ustream'}], 'event_name': u'Present Test Event', 'event_key': u'2014testpresent'}]

var webcastData = $.parseJSON($("#webcasts_json").text().replace(/u'/g,'\'').replace(/'/g,'"'));

ReactDOM.render(
  <GamedayFrame webcastData={webcastData} pollInterval={20000} />,
  document.getElementById('content')
);
