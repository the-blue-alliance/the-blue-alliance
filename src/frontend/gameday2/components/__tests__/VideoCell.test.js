/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent } from "@testing-library/react";

// Mock the connected children so the cell can be exercised without a store;
// each mock surfaces the props/callbacks it receives through the DOM.
jest.mock("../../containers/LivescoreDisplayContainer", () => (props) => (
  <div data-testid="livescore" data-webcast-id={props.webcast.id} />
));
jest.mock("../../containers/VideoCellToolbarContainer", () => (props) => (
  <div data-testid="toolbar" data-bluezone={String(props.isBlueZone)}>
    <button onClick={props.onRequestSelectWebcast}>select</button>
    <button onClick={props.onRequestSwapPosition}>swap</button>
    <button onClick={props.onRequestLiveScoresToggle}>livescore</button>
  </div>
));
jest.mock("../../containers/WebcastSelectionDialogContainer", () => (props) => (
  <div data-testid="webcast-dialog" data-open={String(props.open)}>
    <button onClick={props.onRequestClose}>close-webcast-dialog</button>
    <button onClick={() => props.onWebcastSelected("2026nyro-0")}>
      pick-webcast
    </button>
  </div>
));
jest.mock("../../containers/SwapPositionDialogContainer", () => (props) => (
  <div
    data-testid="swap-dialog"
    data-open={String(props.open)}
    data-position={props.position}
  >
    <button onClick={props.onRequestClose}>close-swap-dialog</button>
  </div>
));
jest.mock("../WebcastEmbed", () => (props) => (
  <div data-testid="embed" data-webcast-id={props.webcast.id} />
));
jest.mock("../VideoCellAnalyticsTracker", () => () => (
  <div data-testid="tracker" />
));

import VideoCell from "../VideoCell";

const webcast = {
  key: "2026casj",
  num: 0,
  id: "2026casj-0",
  name: "Silicon Valley Regional",
  type: "youtube",
  channel: "abc",
};

const renderCell = (props = {}) => {
  const allProps = {
    webcast,
    webcasts: ["2026casj-0", "2026nyro-0"],
    displayedWebcasts: ["2026casj-0", null, null, null],
    layoutId: 3,
    position: 1,
    livescoreOn: false,
    addWebcastAtPosition: jest.fn(),
    swapWebcasts: jest.fn(),
    togglePositionLivescore: jest.fn(),
    ...props,
  };
  const utils = render(<VideoCell {...allProps} />);
  return { ...utils, props: allProps };
};

describe("VideoCell", () => {
  describe("with a webcast", () => {
    it("embeds the webcast, its toolbar, both dialogs and the tracker", () => {
      const { getByTestId, queryByTestId, container } = renderCell();
      expect(getByTestId("embed").getAttribute("data-webcast-id")).toBe(
        "2026casj-0"
      );
      expect(queryByTestId("livescore")).toBeNull();
      expect(getByTestId("toolbar").getAttribute("data-bluezone")).toBe(
        "false"
      );
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "false"
      );
      expect(getByTestId("swap-dialog").getAttribute("data-open")).toBe(
        "false"
      );
      expect(getByTestId("swap-dialog").getAttribute("data-position")).toBe(
        "1"
      );
      expect(getByTestId("tracker")).toBeTruthy();

      // Cell is positioned by the layout (quad view, position 1) with room
      // for the toolbar
      const cell = container.firstChild;
      expect(cell.style.position).toBe("absolute");
      expect(cell.style.paddingBottom).toBe("48px");
      expect(cell.style.outline).toBe("#fff solid 1px");
    });

    it("shows live scores instead of the embed when enabled", () => {
      const { getByTestId, queryByTestId } = renderCell({ livescoreOn: true });
      expect(getByTestId("livescore").getAttribute("data-webcast-id")).toBe(
        "2026casj-0"
      );
      expect(queryByTestId("embed")).toBeNull();
    });

    it("flags the BlueZone webcast to the toolbar", () => {
      const { getByTestId } = renderCell({
        webcast: { ...webcast, key: "bluezone", id: "bluezone-0" },
      });
      expect(getByTestId("toolbar").getAttribute("data-bluezone")).toBe("true");
    });

    it("opens and closes the webcast selection dialog", () => {
      const { getByText, getByTestId } = renderCell();
      fireEvent.click(getByText("select"));
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "true"
      );
      fireEvent.click(getByText("close-webcast-dialog"));
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("adds the chosen webcast at this position and closes the dialog", () => {
      const { getByText, getByTestId, props } = renderCell();
      fireEvent.click(getByText("select"));
      fireEvent.click(getByText("pick-webcast"));
      expect(props.addWebcastAtPosition).toHaveBeenCalledWith("2026nyro-0", 1);
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("swaps directly in two-view layouts", () => {
      const { getByText, getByTestId, props } = renderCell({ layoutId: 1 });
      fireEvent.click(getByText("swap"));
      expect(props.swapWebcasts).toHaveBeenCalledWith(0, 1);
      expect(getByTestId("swap-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("opens the swap dialog in larger layouts and closes it on request", () => {
      const { getByText, getByTestId, props } = renderCell({ layoutId: 3 });
      fireEvent.click(getByText("swap"));
      expect(props.swapWebcasts).not.toHaveBeenCalled();
      expect(getByTestId("swap-dialog").getAttribute("data-open")).toBe("true");
      fireEvent.click(getByText("close-swap-dialog"));
      expect(getByTestId("swap-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("toggles live scores for this position", () => {
      const { getByText, props } = renderCell({ position: 2 });
      fireEvent.click(getByText("livescore"));
      expect(props.togglePositionLivescore).toHaveBeenCalledWith(2);
    });
  });

  describe("without a webcast", () => {
    it("offers to select a webcast when some are still available", () => {
      const { getByText, getByTestId, queryByTestId } = renderCell({
        webcast: null,
      });
      const button = getByText("Select a webcast").closest("button");
      expect(button.disabled).toBe(false);
      expect(queryByTestId("toolbar")).toBeNull();
      expect(queryByTestId("tracker")).toBeNull();

      fireEvent.click(button);
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "true"
      );
      fireEvent.click(getByText("close-webcast-dialog"));
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("adds the chosen webcast at this position", () => {
      const { getByText, getByTestId, props } = renderCell({
        webcast: null,
        position: 3,
      });
      fireEvent.click(getByText("Select a webcast"));
      fireEvent.click(getByText("pick-webcast"));
      expect(props.addWebcastAtPosition).toHaveBeenCalledWith("2026nyro-0", 3);
      expect(getByTestId("webcast-dialog").getAttribute("data-open")).toBe(
        "false"
      );
    });

    it("disables the button when every webcast is already displayed", () => {
      const { getByText } = renderCell({
        webcast: null,
        webcasts: ["2026casj-0", "2026nyro-0"],
        displayedWebcasts: ["2026casj-0", "2026nyro-0", null, null],
      });
      const button = getByText("No more webcasts available").closest("button");
      expect(button.disabled).toBe(true);
    });
  });
});
