import React from 'react'
import ReactDOM from 'react-dom'
import { Provider } from 'react-redux'
import { createStore, applyMiddleware, compose } from 'redux'
import thunk from 'redux-thunk'
import EventWizardFrame from './components/EventWizardFrame'
import eventwizardReducer from './reducers'

const store = createStore(eventwizardReducer, compose(
  applyMiddleware(thunk),
  window.devToolsExtension ? window.devToolsExtension() : (f) => f
))

ReactDOM.render(
  <Provider store={store}>
    <EventWizardFrame />
  </Provider>,
  document.getElementById('content')
)
