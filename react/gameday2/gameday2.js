import 'babel-polyfill'
import React from 'react'
import { Provider } from 'react-redux'
import thunk from 'redux-thunk'
import { createStore, applyMiddleware, compose } from 'redux'
import ReactDOM from 'react-dom'
import queryString from 'query-string'
import injectTapEventPlugin from 'react-tap-event-plugin'
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider'
import { indigo500, indigo700 } from 'material-ui/styles/colors'
import getMuiTheme from 'material-ui/styles/getMuiTheme'
import GamedayFrame from './components/GamedayFrame'
import { firedux } from './reducers'
import gamedayReducer from './reducers'
import { setWebcastsRaw, setLayout, addWebcastAtPosition, setTwitchChat, setChatSidebarVisibility, setFavoriteTeams } from './actions'
import { MAX_SUPPORTED_VIEWS } from './constants/LayoutConstants'

injectTapEventPlugin()

const webcastData = JSON.parse(document.getElementById('webcasts_json').innerHTML)

const store = createStore(gamedayReducer, compose(
  applyMiddleware(thunk),
  window.devToolsExtension ? window.devToolsExtension() : (f) => f
))
firedux.dispatch = store.dispatch

const muiTheme = getMuiTheme({
  palette: {
    primary1Color: indigo500,
    primary2Color: indigo700,
  },
  layout: {
    appBarHeight: 36,
    socialPanelWidth: 300,
    chatPanelWidth: 300,
  },
})

ReactDOM.render(
  <MuiThemeProvider muiTheme={muiTheme}>
    <Provider store={store}>
      <GamedayFrame />
    </Provider>
  </MuiThemeProvider>,
  document.getElementById('content')
)

// Subscribe changes in state.videoGrid.displayed to watch the correct Firebase paths
var lastDisplayed = [];
var subscribedEvents = new Set()
store.subscribe(() => {
  const state = store.getState()

  // See what got added or removed
  let a = new Set(lastDisplayed)
  let b = new Set(state.videoGrid.displayed)
  let added = new Set([...b].filter(x => !a.has(x)))
  let removed = new Set([...a].filter(x => !b.has(x)))

  // Subscribe to added event if not already added
  added.forEach(function (webcastKey) {
    let eventKey = state.webcastsById[webcastKey].key
    if (!subscribedEvents.has(eventKey)) {
      console.log("Subscribing Firebase to:", eventKey)
      subscribedEvents.add(eventKey)

      firedux.watch(`events/${eventKey}/matches`)
      .then(({snapshot}) => {})
    }
  })

  // Unsubscribe from removed event if no more existing
  removed.forEach(function (webcastKey) {
    let existingEventKeys = new Set()
    for (var i in state.videoGrid.displayed) {
      existingEventKeys.add(state.webcastsById[state.videoGrid.displayed[i]].key)
    }

    let eventKey = state.webcastsById[webcastKey].key
    if (!existingEventKeys.has(eventKey)) {
      console.log("Unsubscribing Firebase from", eventKey)
      subscribedEvents.delete(eventKey)

      firedux.ref.child(`events/${eventKey}/matches`).off('value')
      firedux.watching[`events/${eventKey}/matches`] = false  // To make firedux.watch work again
    }
  })

  // Something changed - save lastDisplayed
  if (added.size > 0 || removed.size > 0) {
    lastDisplayed = state.videoGrid.displayed
  }
})

store.dispatch(setWebcastsRaw(webcastData))

// Now that webcasts are loaded, attempt to restore any state that's present in
// the URL hash
const params = queryString.parse(location.hash)
if (params.layout && Number.isInteger(Number.parseInt(params.layout, 10))) {
  store.dispatch(setLayout(Number.parseInt(params.layout, 10)))
}
for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
  const key = `view_${i}`
  if (params[key]) {
    store.dispatch(addWebcastAtPosition(params[key], i))
  }
}
if (params.chat) {
  store.dispatch(setChatSidebarVisibility(true))
  store.dispatch(setTwitchChat(params.chat))
}

// Subscribe to the store to keep the url hash in sync
store.subscribe(() => {
  const newParams = {}

  const state = store.getState()

  const {
    videoGrid: {
      layoutId,
      layoutSet,
      positionMap,
      domOrder,
    },
    chats: {
      currentChat,
    },
    visibility: {
      chatSidebar,
    },
  } = state

  // Which layout is currently active
  if (layoutSet) {
    newParams.layout = layoutId
  }

  // Positions of all webcasts
  for (let i = 0; i < positionMap.length; i++) {
    if (domOrder[positionMap[i]]) {
      newParams[`view_${i}`] = domOrder[positionMap[i]]
    }
  }

  // Chat sidebar
  if (chatSidebar) {
    newParams.chat = currentChat
  }

  const query = queryString.stringify(newParams)
  if (query) {
    location.replace(`#${query}`)
  }
})

// Load myTBA Favorites
fetch('/_/account/favorites/1', {
  credentials: 'same-origin',
}).then(function (response) {
  if (response.status == 200) {
    return response.json()
  } else {
    return null
  }
}).then(json => store.dispatch(setFavoriteTeams(json)))
