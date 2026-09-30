/* @jest-environment jsdom */
import React from "react";
import { render, fireEvent, act } from "@testing-library/react";
import LayoutSelectionPanel from "../LayoutSelectionPanel";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../../constants/LayoutConstants";

// jsdom does no layout, so offsetHeight is derived from the element's role in
// the panel: the full-size outer component, the title, or the list wrapper.
// Tests set `heights` before rendering so componentDidMount measures them too.
let heights = { component: 0, title: 0, list: 0 };
const originalOffsetHeight = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "offsetHeight"
);

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get() {
      if (this.tagName === "H3") {
        return heights.title;
      }
      if (this.style.height === "100%" && this.style.width === "100%") {
        return heights.component;
      }
      if (this.firstChild && this.firstChild.tagName === "UL") {
        return heights.list;
      }
      return 0;
    },
  });
});

afterAll(() => {
  Object.defineProperty(
    HTMLElement.prototype,
    "offsetHeight",
    originalOffsetHeight
  );
});

beforeEach(() => {
  heights = { component: 1000, title: 60, list: 500 };
});

const getListContainer = (container) =>
  container.querySelector("h3").nextSibling;

describe("LayoutSelectionPanel", () => {
  it("lists every layout in display order with its icon", () => {
    const { container, getByText } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    expect(getByText("Select a layout")).toBeTruthy();
    const items = container.querySelectorAll("ul > li");
    expect(items).toHaveLength(NUM_LAYOUTS);
    items.forEach((item, i) => {
      expect(item.textContent).toBe(NAME_FOR_LAYOUT[LAYOUT_DISPLAY_ORDER[i]]);
      expect(item.querySelector("svg path")).not.toBeNull();
    });
  });

  it("Bug #37: offers every layout in LAYOUT_DISPLAY_ORDER, including Nona-View", () => {
    // Wrong today: NUM_LAYOUTS is 12 but 13 layouts are defined, so the last
    // display-order entry (layout 8, Nona-View) is never offered.
    // Correct: every layout in LAYOUT_DISPLAY_ORDER is listed.
    const { container, queryByText } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    expect(container.querySelectorAll("ul > li")).toHaveLength(
      LAYOUT_DISPLAY_ORDER.length
    );
    expect(queryByText("Nona-View")).not.toBeNull();
  });

  it("selects a layout when its item is clicked", () => {
    const setLayout = jest.fn();
    const { getByText } = render(
      <LayoutSelectionPanel setLayout={setLayout} />
    );
    fireEvent.click(getByText("Horizontal Split View"));
    expect(setLayout).toHaveBeenCalledWith(9);
  });

  it("leaves the list unconstrained when it fits within the panel", () => {
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    expect(listContainer.style.height).toBe("");
    expect(listContainer.style.overflowY).toBe("");
  });

  it("constrains and scrolls the list when it overflows the panel", () => {
    heights = { component: 400, title: 60, list: 500 };
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    // 400 - 2 * 20 margin - 60 title = 300
    expect(listContainer.style.height).toBe("300px");
    expect(listContainer.style.overflowY).toBe("auto");
  });

  it("re-measures on window resize", () => {
    const { container } = render(<LayoutSelectionPanel setLayout={() => {}} />);
    const listContainer = getListContainer(container);
    expect(listContainer.style.height).toBe("");

    heights = { component: 400, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("300px");

    // Growing the panel releases the height constraint again
    heights = { component: 1000, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("");
  });

  it("re-measures after re-rendering", () => {
    const { container, rerender } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    const listContainer = getListContainer(container);
    heights = { component: 400, title: 60, list: 500 };
    rerender(<LayoutSelectionPanel setLayout={() => {}} />);
    expect(listContainer.style.height).toBe("300px");
  });

  it("stops listening for resizes after unmount", () => {
    const { container, unmount } = render(
      <LayoutSelectionPanel setLayout={() => {}} />
    );
    const listContainer = getListContainer(container);
    unmount();
    heights = { component: 400, title: 60, list: 500 };
    act(() => {
      window.dispatchEvent(new Event("resize"));
    });
    expect(listContainer.style.height).toBe("");
  });
});
