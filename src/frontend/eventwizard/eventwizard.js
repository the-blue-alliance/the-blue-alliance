import "./eventwizard.less";

import React from "react";
import ReactDOM from "react-dom";
import { Provider } from "react-redux";
import { createStore, applyMiddleware, compose } from "redux";
import thunk from "redux-thunk";
import EventWizardFrame from "./components/EventWizardFrame";
import eventwizardReducer from "./reducers";

const store = createStore(
  eventwizardReducer,
  compose(
    applyMiddleware(thunk),
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
  )
);

ReactDOM.render(
  <Provider store={store}>
    <EventWizardFrame />
  </Provider>,
  document.getElementById("content")
);
