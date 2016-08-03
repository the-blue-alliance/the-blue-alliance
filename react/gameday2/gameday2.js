import 'babel-polyfill'
import React from 'react'
import GamedayFrame from './components/GamedayFrame'
import gamedayReducer from './reducers'
import { Provider } from 'react-redux'
import thunk from 'redux-thunk'
import { createStore, applyMiddleware } from 'redux'
import { setWebcastsRaw, setLayout, addWebcastAtLocation } from './actions'
import { MAX_SUPPORTED_VIEWS } from './constants/LayoutConstants'
var ReactDOM = require('react-dom')
const queryString = require('query-string')

let webcastData = $.parseJSON($("#webcasts_json").text())

let store = createStore(gamedayReducer, applyMiddleware(thunk))

ReactDOM.render(
  <Provider store={store}>
    <GamedayFrame />
  </Provider>,
  document.getElementById('content')
)

store.subscribe(() => {
  let params = {}

  let state = store.getState()
  let layout = state.layout
  if (layout && layout.layoutSet) {
    params.layout = layout.layoutId
  }

  let displayedWebcasts = state.displayedWebcasts
  if (displayedWebcasts) {
    for (let i = 0; i < displayedWebcasts.length; i++) {
      if (displayedWebcasts[i]) {
        params['view_' + i] = displayedWebcasts[i]
      }
    }
  }

  let query = queryString.stringify(params)
  if (query) {
    location.replace('#' + query)
  }
})

// store.dispatch(setWebcastsRaw(webcastData))

// Now that webcasts are loaded, attempt to restore any state that's present in
// the URL hash
let params = queryString.parse(location.hash)
console.log(params)
if (params.layout && Number.isInteger(Number.parseInt(params.layout))) {
  store.dispatch(setLayout(Number.parseInt(params.layout)))
}

for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
  let key = 'view_' + i
  if (params[key]) {
    store.dispatch(addWebcastAtLocation(params[key], i))
  }
}
