import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { Provider } from "react-redux";
import { createStore } from "redux";
// Mock container-level connected components that reach deep into the store
// (VideoCellContainer and VideoCellToolbarContainer) so this unit test can
// focus on MainContent behavior without replicating the whole app state.
// Mock the lower-level presentational components instead of the container
// modules. This avoids having to mock connected module resolution and keeps
// mocks portable across machines.
jest.mock("../VideoCell", () => (props) => (
  <div
    data-testid="video-cell"
    data-has-webcast={props && props.webcast ? "true" : "false"}
    data-webcast-id={props && props.webcast ? props.webcast.id : ""}
  />
));
jest.mock("../VideoCellToolbar", () => () => <div />);

import MainContent from "../MainContent";

describe("MainContent", () => {
  it("renders the layout selector when webcasts exist but layout is not set", () => {
    const theme = createTheme({
      layout: {
        appBarHeight: 36,
        socialPanelWidth: 300,
        chatPanelWidth: 300,
      },
    });

    const html = renderToStaticMarkup(
      <ThemeProvider theme={theme}>
        <MainContent
          webcasts={["webcast_1"]}
          hashtagSidebarVisible={false}
          chatSidebarVisible={false}
          layoutSet={false}
          setLayout={() => {}}
        />
      </ThemeProvider>
    );

    // The LayoutSelectionPanel includes a heading with this text
    expect(html).toContain("Select a layout");
  });

  it("renders the video grid when a layout is selected", () => {
    const theme = createTheme({
      layout: {
        appBarHeight: 36,
        socialPanelWidth: 300,
        chatPanelWidth: 300,
      },
    });
    // Create a minimal Redux store with the keys the VideoGridContainer expects
    // so the connected component can render during this server-side render.
    const initialState = {
      webcastsById: {
        webcast_1: {
          key: "webcast_1",
          num: 1,
          id: "webcast_1",
          name: "Alpha",
          type: "youtube",
          channel: "c1",
        },
      },
      videoGrid: {
        // domOrder contains one webcast and one empty slot (null) so the
        // VideoGrid will render a VideoCellContainer for the empty cell with
        // webcast set to null.
        domOrder: ["webcast_1", null],
        positionMap: [0, -1],
        domOrderLivescoreOn: [false, false],
        // Use layoutId 1 which supports 2 views so the empty slot will be
        // considered when computing emptyCellPositions.
        layoutId: 1,
      },
    };

    const store = createStore((s = initialState) => s, initialState);

    const html = renderToStaticMarkup(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <MainContent
            webcasts={["webcast_1", "webcast_2"]}
            hashtagSidebarVisible={false}
            chatSidebarVisible={false}
            layoutSet={true}
            setLayout={() => {}}
          />
        </ThemeProvider>
      </Provider>
    );

    // The VideoGrid container should be present
    expect(html).toContain('<div style="width:100%;height:100%">');

    // At least one VideoCell should be present with no webcast set (empty cell)
    // — our mocked VideoCellContainer exposes this via data-has-webcast.
    expect(html).toContain('data-has-webcast="false"');
  });
});
