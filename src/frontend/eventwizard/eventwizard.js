import "./eventwizard.less";

import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { createStore, applyMiddleware, compose } from "redux";
import { thunk } from "redux-thunk";
import EventWizardFrame from "./components/EventWizardFrame";
import eventwizardReducer from "./reducers";

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;
const store = createStore(
  eventwizardReducer,
  composeEnhancers(applyMiddleware(thunk))
);

const container = document.getElementById("content");
const root = createRoot(container);
root.render(
  <Provider store={store}>
    <EventWizardFrame />
  </Provider>
);
