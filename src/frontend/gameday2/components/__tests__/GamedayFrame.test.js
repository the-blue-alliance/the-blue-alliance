/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";

// The frame only composes connected containers; mock them so this test does
// not need the whole store.
jest.mock("../../containers/AppBarContainer", () => () => (
  <div data-testid="app-bar" />
));
jest.mock("../../containers/MainContentContainer", () => () => (
  <div data-testid="main-content" />
));
jest.mock("../../containers/ChatSidebarContainer", () => () => (
  <div data-testid="chat-sidebar" />
));
jest.mock("../../containers/HashtagSidebarContainer", () => () => (
  <div data-testid="hashtag-sidebar" />
));

import GamedayFrame from "../GamedayFrame";

describe("GamedayFrame", () => {
  it("composes the app bar, sidebars and main content", () => {
    const { container, getByTestId } = render(<GamedayFrame />);
    expect(container.firstChild.className).toBe("gameday container-full");
    expect(getByTestId("app-bar")).toBeTruthy();
    expect(getByTestId("hashtag-sidebar")).toBeTruthy();
    expect(getByTestId("chat-sidebar")).toBeTruthy();
    expect(getByTestId("main-content")).toBeTruthy();
  });
});
