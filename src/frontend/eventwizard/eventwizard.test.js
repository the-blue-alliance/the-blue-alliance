import React from "react";
import { render, screen } from "@testing-library/react";
import { rest } from "msw";
import { setupServer } from "msw/node";
import { Provider } from "react-redux";
import configureMockStore from "redux-mock-store";
import "@testing-library/jest-dom/extend-expect";

import { defaultState } from "./reducers/auth";
import EventWizardFrame from "./components/EventWizardFrame";

const mockStore = configureMockStore();

const server = setupServer(
  // Mock out API requsts we require
  rest.get("/_/typeahead/teams-all", (req, res, ctx) => {
    return res(ctx.json([]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

it("renders without crashing", () => {
  const initialState = {
    auth: defaultState,
  };
  const store = mockStore(initialState);

  render(
    <Provider store={store}>
      <EventWizardFrame />
    </Provider>
  );

  expect(screen.getAllByRole("heading")[0]).toHaveTextContent(
    /^TBA Event Wizard$/
  );
});
