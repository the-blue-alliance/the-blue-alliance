import "./eventwizard.less";

import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { createStore, applyMiddleware, compose } from "redux";
import { thunk } from "redux-thunk";
import EventWizardFrame from "./components/EventWizardFrame";
import eventwizardReducer from "./reducers";

// Redux DevTools extension support
declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: typeof compose;
  }
}

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
// @ts-ignore - Redux type inference complexity
const store = createStore(
  eventwizardReducer,
  composeEnhancers(applyMiddleware(thunk))
);

const container = document.getElementById("content");
if (!container) {
  throw new Error("Could not find content element to mount React app");
}

const root = createRoot(container);
root.render(
  <Provider store={store}>
    <EventWizardFrame />
  </Provider>
);
