import React from 'react';
import GamedayFrame from './components/GamedayFrame';
import gamedayReducer from './reducers'
import { Provider } from 'react-redux'
import { createStore } from 'redux';
import { setWebcastsRaw } from './actions'
var ReactDOM = require('react-dom');

// [{'webcasts': [{u'channel': u'6540154', u'type': u'ustream'}], 'event_name': u'Present Test Event', 'event_key': u'2014testpresent'}]

let webcastData = $.parseJSON($("#webcasts_json").text());

let store = createStore(gamedayReducer)

ReactDOM.render(
  <Provider store={store}>
    <GamedayFrame />
  </Provider>,
  document.getElementById('content')
);

store.subscribe(() => {
  console.log(store.getState())
})

store.dispatch(setWebcastsRaw(webcastData))
