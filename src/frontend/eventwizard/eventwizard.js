import "./eventwizard.less";

import { configureStore } from "@reduxjs/toolkit";
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import EventWizardFrame from "./components/EventWizardFrame";
import eventwizardReducer from "./reducers";

const store = configureStore({
  reducer: eventwizardReducer,
});

const container = document.getElementById("content");
const root = createRoot(container);
root.render(
  <Provider store={store}>
    <EventWizardFrame />
  </Provider>
);
