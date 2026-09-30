/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";

jest.mock("../../containers/VideoCellContainer", () => (props) => (
  <div
    data-testid="cell"
    data-position={props.position}
    data-webcast-id={props.webcast ? props.webcast.id : ""}
    data-livescore={String(props.livescoreOn)}
  />
));
jest.mock("../LayoutAnalyticsTracker", () => (props) => (
  <div data-testid="tracker" data-layout-id={props.layoutId} />
));

import VideoGrid from "../VideoGrid";

const webcastsById = {
  a: { key: "a", num: 0, id: "a", name: "A", type: "youtube", channel: "a" },
  b: { key: "b", num: 0, id: "b", name: "B", type: "youtube", channel: "b" },
};

describe("VideoGrid", () => {
  it("renders a cell for each webcast at its mapped position, plus empty cells for unused positions", () => {
    // Quad view: webcast b is shown at position 0, a at position 2, and
    // positions 1 and 3 are empty.
    const { getAllByTestId, getByTestId } = render(
      <VideoGrid
        domOrder={["a", "b", null, null]}
        positionMap={[1, -1, 0, -1]}
        domOrderLivescoreOn={[true, false, false, false]}
        webcastsById={webcastsById}
        layoutId={3}
      />
    );
    const cells = getAllByTestId("cell");
    expect(cells).toHaveLength(4);
    expect(cells[0].getAttribute("data-webcast-id")).toBe("a");
    expect(cells[0].getAttribute("data-position")).toBe("2");
    expect(cells[0].getAttribute("data-livescore")).toBe("true");
    expect(cells[1].getAttribute("data-webcast-id")).toBe("b");
    expect(cells[1].getAttribute("data-position")).toBe("0");
    expect(cells[1].getAttribute("data-livescore")).toBe("false");
    // Empty DOM slots take the empty positions in order
    expect(cells[2].getAttribute("data-webcast-id")).toBe("");
    expect(cells[2].getAttribute("data-position")).toBe("1");
    expect(cells[3].getAttribute("data-position")).toBe("3");
    expect(getByTestId("tracker").getAttribute("data-layout-id")).toBe("3");
  });

  it("renders placeholder divs for DOM slots beyond the layout's view count", () => {
    // Single view: only position 0 is visible, so the three empty DOM slots
    // have no position to fill and become plain placeholders.
    const { getAllByTestId, container } = render(
      <VideoGrid
        domOrder={["a", null, null, null]}
        positionMap={[0, -1, -1, -1]}
        domOrderLivescoreOn={[false, false, false, false]}
        webcastsById={webcastsById}
        layoutId={0}
      />
    );
    expect(getAllByTestId("cell")).toHaveLength(1);
    const grid = container.firstChild;
    expect(grid.style.width).toBe("100%");
    expect(grid.style.height).toBe("100%");
    // 1 cell + 3 placeholders + tracker
    expect(grid.children).toHaveLength(5);
    expect(grid.children[1].innerHTML).toBe("");
  });

  it("falls back to a single view for unknown layout ids", () => {
    const { getAllByTestId } = render(
      <VideoGrid
        domOrder={[null, null]}
        positionMap={[-1, -1]}
        domOrderLivescoreOn={[false, false]}
        webcastsById={webcastsById}
        layoutId={99}
      />
    );
    expect(getAllByTestId("cell")).toHaveLength(1);
  });
});
