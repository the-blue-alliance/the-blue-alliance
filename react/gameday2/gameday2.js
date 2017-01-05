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
import gamedayReducer from './reducers'
import { setWebcastsRaw, setLayout, addWebcastAtPosition, setTwitchChat, setChatSidebarVisibility } from './actions'
import { MAX_SUPPORTED_VIEWS } from './constants/LayoutConstants'

injectTapEventPlugin()

const webcastData = JSON.parse(document.getElementById('webcasts_json').innerHTML)

const store = createStore(gamedayReducer, compose(
  applyMiddleware(thunk),
  window.devToolsExtension ? window.devToolsExtension() : (f) => f
))

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
